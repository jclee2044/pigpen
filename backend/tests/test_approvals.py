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
