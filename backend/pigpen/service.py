"""Application services own transactions; HTTP handlers never implement rules."""
from hashlib import sha256
import json
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select, insert, update, func
from sqlalchemy.exc import IntegrityError, OperationalError
from . import schema as s
from .errors import DomainError
from .records import now, get, expect, avatar_options
from .budget import BudgetServices
from .finance import FinanceServices
from .approvals import ApprovalServices
from .notifications import NotificationServices
from .attachments import AttachmentServices
from .push import PushServices


class Service(BudgetServices, FinanceServices, ApprovalServices, NotificationServices, AttachmentServices, PushServices):
    def __init__(self, db):
        self.db = db

    def execute(self, operation):
        op = operation.model_dump(mode='json')
        # Preserve hashes of category commands saved by clients before 0009.
        digest_op = {**op, 'data': dict(op['data'])}
        if op['kind'] == 'category.create' and not op['data']['allows_subcategories']:
            digest_op['data'].pop('allows_subcategories')
        elif op['kind'] == 'category.update' and op['data']['allows_subcategories'] is None:
            digest_op['data'].pop('allows_subcategories')
        digest = sha256(json.dumps(digest_op, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        try:
            with self.db.transaction(write=True) as conn:
                prior = conn.execute(select(s.operations).where(s.operations.c.id == op['operation_id'])).mappings().first()
                if prior:
                    if prior['payload_hash'] != digest:
                        raise DomainError('operation_conflict', 'Operation ID already used with different content', 409)
                    return prior['outcome']
                if op['kind'] != 'household.initialize':
                    self.household(conn)
                if op['kind'] not in {'household.initialize', 'user.create'} or op['actor_id']:
                    get(conn, s.users, op['actor_id'], active=True)
                result = getattr(self, 'do_' + op['kind'].replace('.', '_'))(conn, op)
                outcome = {'operation_id': op['operation_id'], 'result': result}
                conn.execute(insert(s.operations).values(id=op['operation_id'], payload_hash=digest, outcome=outcome, created_at=now()))
                conn.execute(insert(s.audit_events).values(operation_id=op['operation_id'], actor_id=op['actor_id'],
                    kind=op['kind'], target_id=op['entity_id'], client_time=op['client_time'], server_time=now()))
                return outcome
        except IntegrityError:
            raise DomainError('constraint', 'A conflicting or invalid record already exists', 409) from None
        except OperationalError:
            raise DomainError('storage_busy', 'Storage temporarily unavailable; retry this operation', 503) from None

    def household(self, conn):
        row = conn.execute(select(s.households)).mappings().first()
        if not row:
            raise DomainError('setup_required', 'Initialize the household first', 409)
        return dict(row)

    def save(self, conn, table, values, current=None):
        timestamp = now()
        if current:
            values = {**current, **values, 'revision': current['revision'] + 1, 'updated_at': timestamp}
            conn.execute(update(table).where(table.c.id == current['id']).values(**values))
        else:
            values = {'household_id': self.household(conn)['id'], 'revision': 1, 'deleted': False,
                      'created_at': timestamp, 'updated_at': timestamp, **values}
            conn.execute(insert(table).values(**values))
        self.changed(conn, table, values)
        return values

    def changed(self, conn, table, record):
        resource = next((k for k, v in s.RESOURCES.items() if v is table), None)
        if resource:
            conn.execute(insert(s.changes).values(resource=resource, record=record))

    def do_household_initialize(self, c, op):
        if c.execute(select(s.households.c.id)).first():
            raise DomainError('already_initialized', 'Household already exists', 409)
        timestamp = now()
        record = dict(id=op['entity_id'], singleton=1, **op['data'], approval_policy='all', category_order=[],
                      revision=1, deleted=False, created_at=timestamp, updated_at=timestamp)
        c.execute(insert(s.households).values(**record))
        self.changed(c, s.households, record)
        for name in ['Housing', 'Food', 'Gas', 'Dates', 'Savings', 'Phone', 'Car insurance', 'Subscriptions']:
            self.save(c, s.categories, dict(id=str(uuid5(NAMESPACE_URL, op['entity_id'] + '/' + name)), name=name,
                kind='savings' if name == 'Savings' else 'expense', owner_id=None, parent_id=None, active=True, allows_subcategories=name=='Subscriptions'))
        return record

    def validate_avatar(self, avatar):
        options = avatar_options()['groups']
        for group, identifier in avatar.items():
            if identifier not in {x['id'] for x in options[group]}:
                raise DomainError('avatar', f'Unknown {group} option')

    def do_user_create(self, c, op):
        data = op['data']
        self.validate_avatar(data['avatar'])
        record = self.save(c, s.users, dict(id=op['entity_id'], **data, name_key=data['name'].casefold(), active=True, wishlist_order=[]))
        self.save(c, s.categories, dict(id=str(uuid5(NAMESPACE_URL, op['entity_id'] + '/personal')), name=data['name']+' Personal',
            kind='personal', owner_id=op['entity_id'], parent_id=None, active=True, allows_subcategories=True))
        return record

    def do_user_update(self, c, op):
        row = get(c, s.users, op['entity_id']); data = dict(op['data']); expect(row, data.pop('expected_revision'))
        self.validate_avatar(data['avatar'])
        if row['id'] != op['actor_id']:
            raise DomainError('actor', 'Only the selected profile can edit itself', 403)
        if not data['active'] and c.execute(select(func.count()).select_from(s.users).where(s.users.c.active == True)).scalar() <= 1:
            raise DomainError('last_profile', 'Keep at least one active profile', 409)
        record = self.save(c, s.users, {**data, 'name_key': data['name'].casefold()}, row)
        if row['active'] != data['active']:
            for category in c.execute(select(s.categories).where(s.categories.c.owner_id == row['id'])).mappings():
                self.save(c, s.categories, {'active': data['active']}, dict(category))
        return record

    def do_category_create(self, c, op):
        data = op['data']
        if data['kind'] == 'savings':
            raise DomainError('category', 'Use the single shared Savings category')
        if data['kind'] == 'personal':
            if not data['parent_id'] or data['owner_id'] != op['actor_id']:
                raise DomainError('category', 'Create Personal subcategories only under your Personal parent')
            parent = get(c, s.categories, data['parent_id'], active=True)
            if parent['kind'] != 'personal' or parent['parent_id'] or parent['owner_id'] != data['owner_id']:
                raise DomainError('category', 'Invalid Personal parent or owner')
        elif data['owner_id']:
            raise DomainError('category', 'Shared categories cannot have an owner')
        elif data['parent_id']:
            parent = get(c, s.categories, data['parent_id'], active=True)
            if parent['kind'] != 'expense' or parent['parent_id'] or not parent['allows_subcategories']:
                raise DomainError('category', 'Choose a shared parent that allows subcategories')
        if data['parent_id'] and data['allows_subcategories']:
            raise DomainError('category', 'Subcategories cannot contain subcategories')
        return self.save(c, s.categories, dict(id=op['entity_id'], **data, active=True))

    def do_category_reorder(self, c, op):
        row = self.household(c)
        if op['entity_id'] != row['id']:
            raise DomainError('category', 'Category order must target the household')
        expect(row, op['data']['expected_revision'])
        ids = op['data']['category_ids']
        available = set(c.execute(select(s.categories.c.id).where(
            s.categories.c.deleted.is_(False), s.categories.c.parent_id.is_(None))).scalars())
        if len(ids) != len(set(ids)) or not set(ids) <= available:
            raise DomainError('category', 'Order must contain unique top-level categories')
        order = ids + [value for value in row['category_order'] if value not in ids and value in available]
        return self.save(c, s.households, {'category_order': order}, row)

    def do_category_update(self, c, op):
        row = get(c, s.categories, op['entity_id']); data = dict(op['data']); expect(row, data.pop('expected_revision'))
        if row['kind'] == 'personal' and row['owner_id'] != op['actor_id']:
            raise DomainError('actor', 'Only the owner can edit a Personal category', 403)
        if row['kind'] == 'personal' and not row['parent_id'] and not data['active']:
            raise DomainError('category', 'Archive the profile to archive its Personal parent')
        allows = data.pop('allows_subcategories', None)
        if allows is not None:
            if allows and (row['parent_id'] or row['kind'] == 'savings'):
                raise DomainError('category', 'Only top-level expense categories can enable subcategories')
            if not allows and row['kind'] == 'personal' and not row['parent_id']:
                raise DomainError('category', 'Personal parents always allow subcategories')
            if not allows and c.execute(select(s.categories.c.id).where(
                    s.categories.c.parent_id == row['id'], s.categories.c.deleted.is_(False))).first():
                raise DomainError('category', 'Keep subcategories enabled while children exist')
            data['allows_subcategories'] = allows
        return self.save(c, s.categories, data, row)
