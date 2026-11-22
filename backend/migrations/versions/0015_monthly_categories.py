"""Monthly membership and inherited plans; preserve every financial record."""
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid5, NAMESPACE_URL
from alembic import op
import sqlalchemy as sa

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None
OTHER_ID = '00000000-0000-5000-8000-000000000001'


def upgrade():
    op.add_column('purchases', sa.Column('category_explanation', sa.String, nullable=False, server_default=''))
    op.create_table('category_months',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('household_id', sa.String, sa.ForeignKey('households.id'), nullable=False),
        sa.Column('revision', sa.Integer, nullable=False), sa.Column('deleted', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.String, nullable=False), sa.Column('updated_at', sa.String, nullable=False),
        sa.Column('month', sa.String, nullable=False, unique=True),
        sa.Column('category_ids', sa.JSON, nullable=False),
        sa.Column('inherited_allocations', sa.JSON, nullable=False),
        sa.Column('inherited_income_minor', sa.Integer, nullable=False))
    c = op.get_bind()
    # Reflect the schema at this migration; later model changes must not break upgrades.
    tables = sa.MetaData()
    tables.reflect(c)
    def rows(name):
        return [dict(x) for x in c.execute(sa.select(tables.tables[name])).mappings()]
    households = rows('households')
    if not households:
        return
    household = households[0]
    timestamp = datetime.now().astimezone().isoformat()
    def save(name, data):
        record = dict(household_id=household['id'], revision=1, deleted=False,
                      created_at=timestamp, updated_at=timestamp, **data)
        c.execute(tables.tables[name].insert().values(**record))
        resource = 'category-months' if name == 'category_months' else name
        c.execute(tables.tables['changes'].insert().values(resource=resource, record=record))
    existing_other = next((x for x in rows('categories') if x['id'] == OTHER_ID), None)
    if existing_other:
        assert existing_other['name'] == 'Other' and existing_other['kind'] == 'expense' and not existing_other['parent_id']
    else:
        save('categories', dict(id=OTHER_ID, name='Other', kind='expense', owner_id=None,
                               parent_id=None, active=True, allows_subcategories=False))
    categories = rows('categories')
    active = {x['id'] for x in categories if x['active'] and not x['deleted']}
    parents = {x['id']: x['parent_id'] for x in categories}
    budgets = [x for x in rows('budget_months') if not x['deleted']]
    allocations = [x for x in rows('allocations') if not x['deleted']]
    purchases = [x for x in rows('purchases') if not x['deleted']]
    financial = purchases + rows('income_entries') + rows('savings_entries')
    months = {x['transaction_date'][:7] for x in financial if not x['deleted']}
    months.update(x['month'] for x in budgets)
    current = datetime.now(ZoneInfo(household['timezone'])).strftime('%Y-%m')
    if months:
        cursor = min(months)
        while cursor <= current:
            months.add(cursor)
            year, month = map(int, cursor.split('-'))
            cursor = f'{year + (month == 12):04d}-{month % 12 + 1:02d}'
    else:
        months.add(current)
    for month in sorted(months):
        explicit = next((x for x in budgets if x['month'] == month), None)
        source = explicit or max((x for x in budgets if x['month'] < month), key=lambda x: x['month'], default=None)
        amounts = [dict(category_id=x['category_id'], amount_minor=x['amount_minor']) for x in allocations
                   if source and x['budget_month_id'] == source['id'] and (explicit or x['category_id'] in active)]
        ids = set(active)
        if month < current:
            ids.update(x['category_id'] for x in amounts)
            ids.update(x['category_id'] for x in purchases if x['transaction_date'][:7] == month)
            ids.update(parents[x] for x in list(ids) if parents.get(x))
        save('category_months', dict(id=str(uuid5(NAMESPACE_URL, household['id'] + '/categories/' + month)),
                                    month=month, category_ids=sorted(ids), inherited_allocations=amounts,
                                    inherited_income_minor=source['expected_income_minor'] if source else 0))


def downgrade():
    raise RuntimeError('Restore a verified backup; preserve post-upgrade writes first')
