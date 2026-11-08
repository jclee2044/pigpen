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
        assert row['revision'] == 4
        assert row['category_order'] == []
