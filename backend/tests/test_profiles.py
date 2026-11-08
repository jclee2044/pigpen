from sqlalchemy import select, func, text
from pigpen import schema as s
from pigpen.database import Database, migrate
from conftest import operation, submit


def test_atomic_profile_and_retry(client, household, settings):
    op = operation('user.create', {'name': 'Alex'})
    first = client.post('/api/v1/operations', json=op)
    assert first.status_code == 200
    assert client.post('/api/v1/operations', json=op).json() == first.json()
    categories = client.get('/api/v1/categories').json()['items']
    assert len([c for c in categories if c['owner_id'] == op['entity_id']]) == 1
    op['data']['name'] = 'Other'
    assert client.post('/api/v1/operations', json=op).status_code == 409
    duplicate = operation('user.create', {'name': 'alex'})
    assert client.post('/api/v1/operations', json=duplicate).status_code == 409
    with Database(settings).transaction() as c:
        assert c.execute(select(func.count()).select_from(s.users)).scalar() == 1
        assert c.execute(select(func.count()).select_from(s.operations)).scalar() == 2


def test_avatar_and_parent_rules(client, users):
    actor=users[0]['id']
    bad = client.post('/api/v1/operations', json=operation('user.create', {'name':'Bad','avatar':{'hat':'missing'}}))
    assert bad.status_code == 422
    categories = client.get('/api/v1/categories').json()['items']
    parent = next(c for c in categories if c['owner_id']==actor)
    child = submit(client,'category.create',dict(name='Books',kind='personal',owner_id=actor,parent_id=parent['id']),actor)
    bad = operation('category.create',dict(name='Nested',kind='personal',owner_id=actor,parent_id=child['id']),actor)
    assert client.post('/api/v1/operations',json=bad).status_code==422
    bad['data']['parent_id']=parent['id'];bad['data']['owner_id']=users[1]['id']
    assert client.post('/api/v1/operations',json=bad).status_code==422
    assert client.get('/api/v1/health').status_code==200


def test_migration_upgrade_preserves_populated_database(settings):
    migrate(settings, '0001')
    with Database(settings).transaction(write=True) as c:
        c.execute(text("INSERT INTO operations VALUES ('keep','hash','{}','now')"))
    migrate(settings)
    with Database(settings).transaction() as c:
        assert c.execute(text("SELECT id FROM operations")).scalar()=='keep'
        assert c.execute(select(func.count()).select_from(s.users)).scalar()==0


def test_shared_category_order_revisions_validation_and_replay(client, household, users):
    actor = users[0]['id']
    categories = client.get('/api/v1/categories').json()['items']
    ids = [row['id'] for row in categories if not row['parent_id']]
    op = operation('category.reorder', {'expected_revision': household['revision'],
        'category_ids': list(reversed(ids))}, actor, household['id'])
    response = client.post('/api/v1/operations', json=op)
    assert response.status_code == 200
    result = response.json()['result']
    assert result['category_order'] == list(reversed(ids))
    assert result['revision'] == household['revision'] + 1
    assert client.post('/api/v1/operations', json=op).json() == response.json()
    assert client.get('/api/v1/sync/snapshot').json()['records']['household'][0]['category_order'] == result['category_order']
    stale = operation('category.reorder', op['data'], users[1]['id'], household['id'])
    assert client.post('/api/v1/operations', json=stale).status_code == 409
    for invalid in [[ids[0], ids[0]], [str(__import__('uuid').uuid4())]]:
        bad = operation('category.reorder', {'expected_revision': result['revision'], 'category_ids': invalid}, actor, household['id'])
        assert client.post('/api/v1/operations', json=bad).status_code == 422
    # A second household member can move a subset; other saved positions survive.
    updated = submit(client, 'category.reorder', {'expected_revision': result['revision'], 'category_ids': [ids[0]]}, users[1]['id'], household['id'])
    assert updated['category_order'] == [ids[0]] + [value for value in result['category_order'] if value != ids[0]]


def test_category_order_migration_preserves_existing_household(settings):
    migrate(settings, '0006')
    with Database(settings).transaction(write=True) as connection:
        connection.execute(text("INSERT INTO households (id,singleton,name,currency,timezone,approval_policy,revision,deleted,created_at,updated_at) VALUES ('existing',1,'Existing household','USD','America/New_York','all',4,0,'before','before')"))
    migrate(settings)
    with Database(settings).transaction() as connection:
        row = connection.execute(select(s.households)).mappings().one()
        assert row['name'] == 'Existing household'
        assert row['revision'] == 5  # Shared wish-order migration publishes the new household metadata.
        assert row['category_order'] == []


def test_shared_subcategories_validation_and_rollup(client, users):
    actor = users[0]['id']
    categories = client.get('/api/v1/categories').json()['items']
    subscriptions = next(c for c in categories if c['name'] == 'Subscriptions')
    assert subscriptions['allows_subcategories']
    child = submit(client, 'category.create', dict(name='Streaming', parent_id=subscriptions['id']), actor)
    assert child['owner_id'] is None and not child['allows_subcategories']
    custom = submit(client, 'category.create', dict(name='Utilities', allows_subcategories=True), actor)
    flat = submit(client, 'category.create', dict(name='Flat'), actor)
    savings = next(c for c in categories if c['kind'] == 'savings')
    for parent, extra in [(child, {}), (flat, {}), (savings, {}), (custom, {'allows_subcategories': True})]:
        bad = operation('category.create', dict(name='Invalid', parent_id=parent['id'], **extra), actor)
        assert client.post('/api/v1/operations', json=bad).status_code == 422
    for row in [child, savings]:
        bad = operation('category.update', dict(name=row['name'], active=True, expected_revision=row['revision'], allows_subcategories=True), actor, row['id'])
        assert client.post('/api/v1/operations', json=bad).status_code == 422
    bad = operation('category.update', dict(name=subscriptions['name'], active=True, expected_revision=subscriptions['revision'], allows_subcategories=False), actor, subscriptions['id'])
    assert client.post('/api/v1/operations', json=bad).status_code == 422
    # Older clients omit the new flag without disabling an enabled parent.
    updated = submit(client, 'category.update', dict(name='Utilities renamed', active=True, expected_revision=custom['revision']), actor, custom['id'])
    assert updated['allows_subcategories']
    submit(client, 'budget.set', dict(month='2026-11', expected_income_minor=10000,
        allocations=[dict(category_id=subscriptions['id'], amount_minor=5000)]), actor)
    for category, amount in [(subscriptions, 1000), (child, 1500)]:
        submit(client, 'purchase.create', dict(item='Synthetic subscription', amount_minor=amount,
            category_id=category['id'], transaction_date='2026-11-08'), actor)
    budget = client.get('/api/v1/budget-months/2026-11').json()
    rollup = next(row for row in budget['categories'] if row['category_id'] == subscriptions['id'])
    assert rollup['actual_minor'] == 2500 and rollup['remaining_minor'] == 2500
    bad = operation('budget.set', dict(month='2026-12', expected_income_minor=10000,
        allocations=[dict(category_id=child['id'], amount_minor=1000)]), actor)
    assert client.post('/api/v1/operations', json=bad).status_code == 422
    archived = submit(client, 'category.update', dict(name=child['name'], active=False, expected_revision=child['revision']), actor, child['id'])
    assert not archived['active']
    assert client.post('/api/v1/operations', json=operation('category.update', dict(name=subscriptions['name'], active=True,
        expected_revision=subscriptions['revision'], allows_subcategories=False), actor, subscriptions['id'])).status_code == 422
    parent = submit(client, 'category.update', dict(name=subscriptions['name'], active=False, expected_revision=subscriptions['revision']), actor, subscriptions['id'])
    assert client.post('/api/v1/operations', json=operation('category.create', dict(name='Archived parent child', parent_id=parent['id']), actor)).status_code == 409


def test_hierarchy_migration_preserves_references_and_publishes_changes(settings):
    migrate(settings, '0008')
    with Database(settings).transaction(write=True) as c:
        common = dict(household_id='house', revision=1, deleted=False, created_at='before', updated_at='before')
        c.execute(s.households.insert().values(id='house', singleton=1, name='House', currency='USD', timezone='America/New_York', approval_policy='all', category_order=[], revision=1, deleted=False, created_at='before', updated_at='before'))
        c.execute(s.users.insert().values(id='alex', name='Alex', name_key='alex', avatar={}, active=True, **common))
        # Use SQL because the pre-0009 table has no allows_subcategories column.
        for identifier, parent in [('personal', None), ('books', 'personal')]:
            c.execute(text('INSERT INTO categories (id,household_id,revision,deleted,created_at,updated_at,name,kind,owner_id,parent_id,active) VALUES (:id,\'house\',1,0,\'before\',\'before\',:id,\'personal\',\'alex\',:parent,1)'), dict(id=identifier, parent=parent))
        c.execute(s.purchases.insert().values(id='purchase', purchaser_id='alex', category_id='books', item='Book', amount_minor=1500, transaction_date='2026-11-08', description='', **common))
        c.execute(s.budget_months.insert().values(id='month', month='2026-11', expected_income_minor=10000, **common))
        c.execute(s.allocations.insert().values(id='allocation', budget_month_id='month', category_id='personal', amount_minor=5000, **common))
    migrate(settings)
    with Database(settings).transaction() as c:
        assert not c.exec_driver_sql('PRAGMA foreign_key_check').first()
        assert c.exec_driver_sql('PRAGMA foreign_keys').scalar() == 1
        categories = {row['id']: dict(row) for row in c.execute(select(s.categories)).mappings()}
        assert categories['personal']['allows_subcategories'] and categories['personal']['revision'] == 2
        assert not categories['books']['allows_subcategories'] and categories['books']['parent_id'] == 'personal'
        assert c.execute(select(s.purchases.c.category_id)).scalar() == 'books'
        assert c.execute(select(s.allocations.c.category_id)).scalar() == 'personal'
        assert any(row['name'] == 'Subscriptions' and row['allows_subcategories'] for row in categories.values())
        records = [row for row in c.execute(select(s.changes.c.record).where(s.changes.c.resource == 'categories')).scalars()]
        assert {row['name'] for row in records} == {'personal', 'Subscriptions'}
    migrate(settings)
    with Database(settings).transaction() as c:
        assert c.execute(select(func.count()).select_from(s.categories)).scalar() == 3


def test_legacy_category_retry_hash_is_preserved(client, users, settings):
    from hashlib import sha256
    import json
    from sqlalchemy import update
    actor = users[0]['id']
    create = operation('category.create', dict(name='Old client category', kind='expense', owner_id=None, parent_id=None), actor)
    first = client.post('/api/v1/operations', json=create)
    assert first.status_code == 200
    category = first.json()['result']
    edit = operation('category.update', dict(name='Old client renamed', active=True, expected_revision=category['revision']), actor, category['id'])
    for command in [create, edit]:
        response = client.post('/api/v1/operations', json=command)
        assert response.status_code == 200
        from pydantic import TypeAdapter
        from pigpen.contracts import Operation
        legacy = TypeAdapter(Operation).validate_python(command).model_dump(mode='json')
        legacy['data'].pop('allows_subcategories')
        legacy_hash = sha256(json.dumps(legacy, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with Database(settings).transaction(write=True) as c:
            c.execute(update(s.operations).where(s.operations.c.id == command['operation_id']).values(payload_hash=legacy_hash))
        assert client.post('/api/v1/operations', json=command).json() == response.json()
