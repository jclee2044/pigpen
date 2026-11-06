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
