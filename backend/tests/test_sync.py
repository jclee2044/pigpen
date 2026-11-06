from uuid import uuid4
from conftest import operation, submit


def test_ordered_replay_original_actor_and_partial_failure(client,users):
    a,b,c=[x['id'] for x in users]
    request=operation('request.create',dict(item='Offline item',amount_minor=500),a)
    vote=operation('vote.set',dict(request_id=request['entity_id'],request_revision=1,approved=True),b)
    bad=operation('vote.set',dict(request_id=request['entity_id'],request_revision=1,approved=True),a)
    batch={'operations':[request,vote,bad]}
    response=client.post('/api/v1/sync/push',json=batch).json()['outcomes']
    assert [r['ok'] for r in response]==[True,True,False]
    assert response[0]['result']['requester_id']==a
    assert response[1]['result']['reviewer_id']==b
    assert client.post('/api/v1/sync/push',json=batch).json()['outcomes']==response
    assert len(client.get('/api/v1/approval-requests').json()['items'])==1


def test_incremental_cursor_tombstones_and_snapshot(client,users):
    actor=users[0]['id']
    snapshot=client.get('/api/v1/sync/snapshot').json()
    category=next(x for x in snapshot['records']['categories'] if x['name']=='Food')
    purchase=submit(client,'purchase.create',dict(item='Offline',amount_minor=100,category_id=category['id'],transaction_date='2026-11-06'),actor)
    submit(client,'purchase.delete',dict(expected_revision=1),actor,purchase['id'])
    cursor=snapshot['cursor'];changes=[]
    while True:
        page=client.get(f'/api/v1/sync/pull?cursor={cursor}&limit=1').json()
        changes+=page['changes'];cursor=page['next_cursor']
        if not page['has_more']:break
    records=[x['record'] for x in changes if x['resource']=='purchases']
    assert [x['revision'] for x in records]==[1,2]
    assert records[-1]['deleted'] is True
    assert records[0]['deleted'] is False
    assert client.get('/api/v1/sync/pull?cursor=999999').status_code==409
    assert client.get('/api/v1/purchases?month=2026-11').json()['items']==[]


def test_archived_actor_and_category_conflicts_keep_original_intent(client,users):
    actor=users[0]['id'];category=next(x for x in client.get('/api/v1/categories').json()['items'] if x['name']=='Food')
    queued=operation('purchase.create',dict(item='Queued',amount_minor=123,category_id=category['id'],transaction_date='2026-10-01'),actor)
    submit(client,'category.update',dict(name='Food',active=False,expected_revision=1),users[1]['id'],category['id'])
    result=client.post('/api/v1/sync/push',json={'operations':[queued]}).json()['outcomes'][0]
    assert not result['ok'] and result['error']['code']=='archived'
    assert client.get('/api/v1/purchases').json()['items']==[]


def test_only_guaranteed_offline_operations_are_replayed(client,users):
    op=operation('category.create',dict(name='Online category'),users[0]['id'])
    result=client.post('/api/v1/sync/push',json={'operations':[op]}).json()['outcomes'][0]
    assert not result['ok'] and result['error']['code']=='online_only'
