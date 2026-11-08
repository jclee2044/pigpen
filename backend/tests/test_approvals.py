from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from conftest import operation, submit
from pigpen.database import Database
from pigpen import schema as s
from pigpen.service import Service
from pydantic import TypeAdapter
from pigpen.contracts import Operation


def create_request(client,actor):
    return submit(client,'request.create',dict(item='Shared item',amount_minor=1000),actor)


def vote(client,request,user):
    return submit(client,'vote.set',dict(request_id=request['id'],request_revision=request['revision'],approved=True),user)


def test_unanimity_independent_reviewers_and_link(client,users):
    a,b,c=[x['id'] for x in users]
    request=create_request(client,a)
    own=operation('vote.set',dict(request_id=request['id'],request_revision=1,approved=True),a)
    assert client.post('/api/v1/operations',json=own).status_code==403
    vote(client,request,b)
    detail='/api/v1/records/approval-requests/'+request['id']
    assert client.get(detail).json()['approved'] is False
    vote(client,request,c)
    assert client.get(detail).json()['approved'] is True
    category=next(x for x in client.get('/api/v1/categories').json()['items'] if x['name']=='Food')
    purchase=dict(item='Actual item',amount_minor=1200,category_id=category['id'],transaction_date='2026-11-06',request_id=request['id'],request_revision=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:client.post('/api/v1/operations',json=operation('purchase.create',purchase,a)),range(2)))
    assert sorted(r.status_code for r in results)==[200,409]
    final=client.get(detail).json()
    assert final['status']=='purchased' and final['approved'] is True and final['approved_revision']==1
    assert len(client.get('/api/v1/purchases').json()['items'])==1
    assert client.post('/api/v1/operations',json=operation('request.delete',dict(expected_revision=final['revision']),a,request['id'])).status_code==409
    late=operation('vote.set',dict(request_id=request['id'],request_revision=1,approved=False),b)
    assert client.post('/api/v1/operations',json=late).status_code==409


def test_request_edits_invalidate_votes_and_duplicate_notifications(client,users):
    a,b,c=[x['id'] for x in users];request=create_request(client,a)
    op=operation('vote.set',dict(request_id=request['id'],request_revision=1,approved=True),b)
    first=client.post('/api/v1/operations',json=op)
    before=len(client.get('/api/v1/notifications?limit=100').json()['items'])
    assert client.post('/api/v1/operations',json=op).json()==first.json()
    assert len(client.get('/api/v1/notifications?limit=100').json()['items'])==before
    submit(client,'request.update',dict(item='Revised',amount_minor=2000,expected_revision=1),a,request['id'])
    detail=client.get('/api/v1/records/approval-requests/'+request['id']).json()
    assert not detail['approved'] and not detail['votes'][0]['approved']
    stale=operation('vote.set',dict(request_id=request['id'],request_revision=1,approved=True),c)
    assert client.post('/api/v1/operations',json=stale).status_code==409


def test_failed_event_rolls_back_domain_and_support_records(client,users,settings,monkeypatch):
    op=TypeAdapter(Operation).validate_python(operation('wishlist.create',dict(name='Test',price_minor=500),users[0]['id']))
    def fail(*args,**kwargs):
        raise RuntimeError('simulated event failure')
    monkeypatch.setattr(Service,'notify',fail)
    with pytest.raises(RuntimeError):
        Service(Database(settings)).execute(op)
    with Database(settings).transaction() as c:
        assert c.execute(select(func.count()).select_from(s.wishlist_items)).scalar()==0
        assert c.execute(select(func.count()).select_from(s.operations).where(s.operations.c.id==str(op.operation_id))).scalar()==0
        assert c.execute(select(func.count()).select_from(s.audit_events).where(s.audit_events.c.operation_id==str(op.operation_id))).scalar()==0


def test_wish_delete_owner_revision_replay_and_sync(client,users):
    owner,other=[x['id'] for x in users[:2]]
    wish=submit(client,'wishlist.create',dict(name='Delete wish',price_minor=500),owner)
    comment=submit(client,'comment.create',dict(target_resource='wishlist-items',target_id=wish['id'],text='Keep history'),other)
    request=create_request(client,owner)
    wrong=operation('wishlist.delete',dict(expected_revision=1),other,wish['id'])
    assert client.post('/api/v1/operations',json=wrong).status_code==403
    submit(client,'wishlist.update',dict(name=wish['name'],price_minor=600,expected_revision=1),owner,wish['id'])
    stale=operation('wishlist.delete',dict(expected_revision=1),owner,wish['id'])
    assert client.post('/api/v1/operations',json=stale).status_code==409
    cursor=client.get('/api/v1/sync/snapshot').json()['cursor']
    op=operation('wishlist.delete',dict(expected_revision=2),owner,wish['id'])
    first=client.post('/api/v1/operations',json=op)
    assert first.status_code==200
    assert first.json()['result']['deleted'] is True
    assert first.json()['result']['revision']==3
    assert client.post('/api/v1/operations',json=op).json()==first.json()
    assert all(x['id']!=wish['id'] for x in client.get('/api/v1/wishlist-items').json()['items'])
    changes=client.get(f'/api/v1/sync/pull?cursor={cursor}').json()['changes']
    assert any(x['resource']=='wishlist-items' and x['record']['id']==wish['id'] and x['record']['deleted'] for x in changes)
    assert client.get('/api/v1/records/comments/'+comment['id']).status_code==200
    assert client.get('/api/v1/records/approval-requests/'+request['id']).status_code==200


def test_request_delete_and_deny_permissions_reason_revision_and_replay(client,users):
    owner,reviewer,other=[x['id'] for x in users]
    request=create_request(client,owner)
    for kind,data,actor in [('request.delete',{},reviewer),('request.deny',{'reason':'No'},owner)]:
        assert client.post('/api/v1/operations',json=operation(kind,dict(expected_revision=1,**data),actor,request['id'])).status_code==403
    for reason in ['', '   ']:
        assert client.post('/api/v1/operations',json=operation('request.deny',dict(expected_revision=1,reason=reason),reviewer,request['id'])).status_code==422
    assert client.post('/api/v1/operations',json=operation('request.deny',dict(expected_revision=2,reason='Too soon'),reviewer,request['id'])).status_code==409
    vote(client,request,reviewer)
    cursor=client.get('/api/v1/sync/snapshot').json()['cursor']
    op=operation('request.deny',dict(expected_revision=1,reason='  Wait until next month.  '),reviewer,request['id'])
    response=client.post('/api/v1/operations',json=op)
    assert response.status_code==200
    assert response.json()['result']['status']=='denied'
    assert client.post('/api/v1/operations',json=op).json()==response.json()
    detail=client.get('/api/v1/records/approval-requests/'+request['id']).json()
    assert detail['approved'] is False
    comments=[x for x in client.get('/api/v1/comments').json()['items'] if x['target_id']==request['id']]
    assert len(comments)==1 and comments[0]['actor_id']==reviewer
    assert comments[0]['text']=='Request denied: Wait until next month.'
    notes=[x for x in client.get('/api/v1/notifications').json()['items'] if x['kind']=='request.denied']
    assert len(notes)==2 and all('Wait until' not in x['message'] for x in notes)
    for kind,data in [('vote.set',dict(request_id=request['id'],request_revision=2,approved=True)),('request.deny',dict(expected_revision=2,reason='No'))]:
        assert client.post('/api/v1/operations',json=operation(kind,data,other,request['id'] if kind=='request.deny' else None)).status_code==409
    changes=client.get(f'/api/v1/sync/pull?cursor={cursor}').json()['changes']
    assert any(x['resource']=='approval-requests' and x['record']['status']=='denied' for x in changes)
    delete=operation('request.delete',dict(expected_revision=2),owner,request['id'])
    first=client.post('/api/v1/operations',json=delete)
    assert first.status_code==200 and first.json()['result']['deleted']
    assert client.post('/api/v1/operations',json=delete).json()==first.json()
    assert all(x['id']!=request['id'] for x in client.get('/api/v1/approval-requests').json()['items'])
    assert client.get('/api/v1/records/comments/'+comments[0]['id']).status_code==200


def test_denial_rolls_back_reason_and_status_on_notification_failure(client,users,settings,monkeypatch):
    request=create_request(client,users[0]['id'])
    op=TypeAdapter(Operation).validate_python(operation('request.deny',dict(expected_revision=1,reason='No'),users[1]['id'],request['id']))
    def fail(*args,**kwargs):
        raise RuntimeError('notification failed')
    monkeypatch.setattr(Service,'notify',fail)
    with pytest.raises(RuntimeError):
        Service(Database(settings)).execute(op)
    assert client.get('/api/v1/records/approval-requests/'+request['id']).json()['status']=='open'
    assert not client.get('/api/v1/comments').json()['items']


def test_denial_migration_preserves_existing_requests_votes_and_replay(settings,monkeypatch):
    from pigpen.database import migrate
    migrate(settings,'0010')
    service=Service(Database(settings))
    def execute(kind,data,actor=None,entity=None):
        return service.execute(TypeAdapter(Operation).validate_python(operation(kind,data,actor,entity)))['result']
    # Simulate the pre-0012 service schema when seeding the historical database.
    from sqlalchemy import MetaData, Table
    legacy_users=Table('users',MetaData(),autoload_with=Database(settings).engine)
    legacy_households=Table('households',MetaData(),autoload_with=Database(settings).engine)
    original_save=Service.save
    def legacy_save(self,c,table,values,current=None):
        return original_save(self,c,table,{key:value for key,value in values.items() if key in table.c},current)
    with monkeypatch.context() as legacy:
        legacy.setattr(s,'households',legacy_households)
        legacy.setitem(s.RESOURCES,'household',legacy_households)
        legacy.setattr(s,'users',legacy_users)
        legacy.setitem(s.RESOURCES,'users',legacy_users)
        legacy.setattr(Service,'save',legacy_save)
        execute('household.initialize',dict(name='Migration household'))
        owner=execute('user.create',dict(name='Owner'))['id']
        reviewer=execute('user.create',dict(name='Reviewer'))['id']
        proposal=execute('request.create',dict(item='Keep request',amount_minor=500),owner)
        vote=execute('vote.set',dict(request_id=proposal['id'],request_revision=1,approved=True),reviewer)
    with Database(settings).transaction() as c:
        before={name:[tuple(row) for row in c.exec_driver_sql('SELECT * FROM '+name)] for name in ['approval_requests','approval_votes','operations','audit_events']}
    migrate(settings)
    with Database(settings).transaction() as c:
        assert not c.exec_driver_sql('PRAGMA foreign_key_check').all()
        for name,rows in before.items():
            assert [tuple(row) for row in c.exec_driver_sql('SELECT * FROM '+name)]==rows
        assert c.execute(select(s.approval_votes.c.id)).scalar()==vote['id']
    denied=execute('request.deny',dict(expected_revision=1,reason='Later'),reviewer,proposal['id'])
    assert denied['status']=='denied'
