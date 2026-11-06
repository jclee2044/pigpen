"""Application services own transactions; HTTP handlers never implement rules."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid4, uuid5, NAMESPACE_URL
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
        digest = sha256(json.dumps(op, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
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
        record = dict(id=op['entity_id'], singleton=1, **op['data'], approval_policy='all',
                      revision=1, deleted=False, created_at=timestamp, updated_at=timestamp)
        c.execute(insert(s.households).values(**record))
        self.changed(c, s.households, record)
        for name in ['Housing', 'Food', 'Gas', 'Dates', 'Savings', 'Phone', 'Car insurance']:
            self.save(c, s.categories, dict(id=str(uuid5(NAMESPACE_URL, op['entity_id'] + '/' + name)), name=name,
                kind='savings' if name == 'Savings' else 'expense', owner_id=None, parent_id=None, active=True))
        return record

    def validate_avatar(self, avatar):
        options = avatar_options()['groups']
        for group, identifier in avatar.items():
            if identifier not in {x['id'] for x in options[group]}:
                raise DomainError('avatar', f'Unknown {group} option')

    def do_user_create(self, c, op):
        data = op['data']
        self.validate_avatar(data['avatar'])
        record = self.save(c, s.users, dict(id=op['entity_id'], **data, name_key=data['name'].casefold(), active=True))
        self.save(c, s.categories, dict(id=str(uuid5(NAMESPACE_URL, op['entity_id'] + '/personal')), name=data['name']+' Personal',
            kind='personal', owner_id=op['entity_id'], parent_id=None, active=True))
        return record

    def do_user_update(self, c, op):
        row = get(c, s.users, op['entity_id']); data = dict(op['data']); expect(row, data.pop('expected_revision'))
        self.validate_avatar(data['avatar'])
        if row['id'] != op['actor_id']:
            raise DomainError('actor', 'Only the selected profile can edit itself', 403)
        if not data['active'] and c.execute(select(func.count()).select_from(s.users).where(s.users.c.active == True)).scalar() <= 1:
            raise DomainError('last_profile', 'Keep at least one active profile', 409)
        record = self.save(c, s.users, {**data, 'name_key': data['name'].casefold()}, row)
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
        elif data['parent_id'] or data['owner_id']:
            raise DomainError('category', 'Only Personal categories have parents or owners')
        return self.save(c, s.categories, dict(id=op['entity_id'], **data, active=True))

    def do_category_update(self, c, op):
        row = get(c, s.categories, op['entity_id']); data = dict(op['data']); expect(row, data.pop('expected_revision'))
        if row['kind'] == 'personal' and row['owner_id'] != op['actor_id']:
            raise DomainError('actor', 'Only the owner can edit a Personal category', 403)
        if row['kind'] == 'personal' and not row['parent_id'] and not data['active']:
            raise DomainError('category', 'Archive the profile to archive its Personal parent')
        return self.save(c, s.categories, data, row)
