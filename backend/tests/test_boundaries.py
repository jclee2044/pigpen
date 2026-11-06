from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import insert, select, text
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from conftest import operation, submit
from pigpen import schema as s
from pigpen.app import create_app
from pigpen.database import Database, migrate
from pigpen.config import Settings
from test_attachments_push import subscription
from pigpen.push import deliver_once


def test_migration_metadata_matches_schema(settings):
    migrate(settings)
    with Database(settings).transaction() as c:
        assert compare_metadata(MigrationContext.configure(c),s.metadata)==[]


def test_restart_retains_replay_outcome_and_notification_read(client,users,settings):
    actor=users[0]['id'];op=operation('wishlist.create',dict(name='Wish',price_minor=100),actor)
    first=client.post('/api/v1/operations',json=op).json()
    with TestClient(create_app(settings)) as restarted:
        assert restarted.post('/api/v1/operations',json=op).json()==first
        notes=restarted.get('/api/v1/notifications',params={'recipient_id':users[1]['id']}).json()['items']
        assert len(notes)==1
        note=submit(restarted,'notification.read',{'expected_revision':1},users[1]['id'],notes[0]['id'])
        assert note['read_at']


def test_successful_device_is_not_resent_when_another_device_retries(client,users,settings):
    a,b,c=[x['id'] for x in users]
    _,one=subscription(client,b,'https://fcm.googleapis.com/fcm/send/one')
    _,two=subscription(client,b,'https://fcm.googleapis.com/fcm/send/two')
    submit(client,'wishlist.create',dict(name='Wish',price_minor=100),a)
    calls=[]
    def sender(sub,payload):
        calls.append(sub['id']);return 200 if sub['id']==one['id'] else 503
    db=Database(settings);assert deliver_once(db,sender)
    with db.transaction(write=True) as conn:
        conn.execute(s.outbox.update().where(s.outbox.c.recipient_id==b).values(next_attempt='2000'))
    assert deliver_once(db,lambda sub,payload:calls.append(sub['id']) or 200)
    assert calls.count(one['id'])==1 and calls.count(two['id'])==2


def test_profile_edit_does_not_unarchive_subcategories(client,users):
    actor=users[0]['id'];parent=next(x for x in client.get('/api/v1/categories').json()['items'] if x['owner_id']==actor)
    child=submit(client,'category.create',dict(name='Books',kind='personal',owner_id=actor,parent_id=parent['id']),actor)
    submit(client,'category.update',dict(name='Books',active=False,expected_revision=1),actor,child['id'])
    submit(client,'user.update',dict(name='Alex renamed',active=True,expected_revision=1),actor,actor)
    assert client.get('/api/v1/records/categories/'+child['id']).json()['active'] is False


def test_shared_budget_alerts_are_deduplicated_and_targeted(client,users):
    actor=users[0]['id'];cats=client.get('/api/v1/categories').json()['items'];food=next(x for x in cats if x['name']=='Food');gas=next(x for x in cats if x['name']=='Gas')
    submit(client,'budget.set',dict(month='2026-11',allocations=[dict(category_id=food['id'],amount_minor=100),dict(category_id=gas['id'],amount_minor=10000)]),actor)
    for amount in [100,1,1]:
        submit(client,'purchase.create',dict(item='Food',amount_minor=amount,category_id=food['id'],transaction_date='2026-11-06'),actor)
    notes=client.get('/api/v1/notifications?limit=100').json()['items']
    assert len(notes)==6 # reached and exceeded, each once per active recipient.
    assert len(set((x['recipient_id'],x['event_key']) for x in notes))==6
    before=len(notes)
    submit(client,'purchase.create',dict(item='Gas',amount_minor=1,category_id=gas['id'],transaction_date='2026-11-06'),actor)
    assert len(client.get('/api/v1/notifications?limit=100').json()['items'])==before


def test_public_contract_documents_typed_operations(client):
    spec=client.get('/openapi.json').json()
    body=spec['paths']['/api/v1/operations']['post']['requestBody']['content']['application/json']['schema']
    assert body['discriminator']['propertyName']=='kind'
    assert 'purchase.create' in body['discriminator']['mapping']


def test_environment_markers_prevent_cross_environment_database_access(settings):
    import pytest
    from pigpen.errors import DomainError
    migrate(settings)
    other=Settings(settings.data_dir,'production')
    assert not Database(other).ready()
    with pytest.raises(DomainError,match='environment'):
        with Database(other).transaction():pass
    with pytest.raises(ValueError,match='environment'):
        migrate(other)


def test_failed_personal_category_creation_rolls_back_profile(client,household,settings):
    from uuid import uuid5, NAMESPACE_URL
    identifier=str(uuid4())
    reserved=str(uuid5(NAMESPACE_URL,identifier+'/personal'))
    with Database(settings).transaction(write=True) as c:
        c.execute(s.categories.update().where(s.categories.c.name=='Gas').values(id=reserved))
    op=operation('user.create',{'name':'No partial profile'},entity=identifier)
    assert client.post('/api/v1/operations',json=op).status_code==409
    assert client.get('/api/v1/users').json()['items']==[]


def test_archived_original_actor_is_not_reassigned(client,users):
    actor=users[0]['id'];category=next(x for x in client.get('/api/v1/categories').json()['items'] if x['name']=='Food')
    queued=operation('purchase.create',dict(item='Queued',amount_minor=100,category_id=category['id'],transaction_date='2026-10-01'),actor)
    submit(client,'user.update',dict(name=users[0]['name'],active=False,expected_revision=1),actor,actor)
    outcome=client.post('/api/v1/sync/push',json={'operations':[queued]}).json()['outcomes'][0]
    assert not outcome['ok'] and outcome['error']['code']=='archived'
    assert client.get('/api/v1/purchases').json()['items']==[]


def test_database_symlink_cannot_bypass_environment_registration(settings,tmp_path):
    import pytest
    from pigpen.errors import DomainError
    migrate(settings)
    settings.database_path.unlink()
    settings.database_path.symlink_to(tmp_path/'other-financials.sqlite3')
    with pytest.raises(ValueError,match='symbolic'):
        settings.verify_storage()
