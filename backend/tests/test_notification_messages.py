from sqlalchemy import select
from conftest import operation,submit
from pigpen import schema as s
from pigpen.database import Database
from pigpen.push import deliver_once


def test_wish_message_is_frozen_and_push_uses_allowlisted_fields(client,users,settings):
    actor,recipient=users[:2]
    op=operation('wishlist.create',{'name':'Switch 2','price_minor':987654,'description':'Private description $9876'},actor['id'])
    assert client.post('/api/v1/operations',json=op).status_code==200
    assert client.post('/api/v1/operations',json=op).status_code==200
    notes=client.get('/api/v1/notifications').json()['items']
    assert len(notes)==2
    expected='Alex just added "Switch 2" to the wish list'
    assert all(n['message']==expected and n['recipient_id']!=actor['id'] for n in notes)
    wish=client.get('/api/v1/wishlist-items').json()['items'][0]
    submit(client,'wishlist.update',dict(expected_revision=wish['revision'],name='Changed',price_minor=123,
        description='New private details',url=None,status='active'),actor['id'],wish['id'])
    from test_attachments_push import subscription
    subscription(client,recipient['id'])
    payloads=[]
    db=Database(settings)
    while deliver_once(db,lambda sub,payload:payloads.append(payload) or 201):pass
    assert len(payloads)==1
    assert payloads[0]['body']==expected
    assert set(payloads[0])=={'notification_id','url','tag','title','body'}
    assert '987654' not in str(payloads) and 'Private' not in str(payloads)
    notes=client.get('/api/v1/sync/snapshot').json()['records']['notifications']
    assert all(n['message']==expected for n in notes)


def test_purchase_and_approval_messages_exclude_financial_fields(client,users):
    actor=users[1]['id']
    category=next(c for c in client.get('/api/v1/categories').json()['items'] if c['name']=='Food')
    request=submit(client,'request.create',dict(item='Lawn chair',amount_minor=876543,description='secret $8765'),actor)
    submit(client,'comment.create',dict(target_resource='approval-requests',target_id=request['id'],text='secret $7654'),users[0]['id'])
    op=operation('purchase.create',dict(item='Lawn chair',amount_minor=654321,category_id=category['id'],
        transaction_date='2026-11-08',merchant='Private merchant',description='secret $6543'),actor)
    first=client.post('/api/v1/operations',json=op)
    assert first.status_code==200,first.text
    assert client.post('/api/v1/operations',json=op).json()==first.json()
    notes=client.get('/api/v1/notifications').json()['items']
    for kind,expected in [('request.created','Sam submitted "Lawn chair" for approval'),
                          ('comment.created','Alex commented on "Lawn chair"'),
                          ('purchase.created','Sam added a purchase: "Lawn chair"')]:
        matching=[n for n in notes if n['kind']==kind]
        assert len(matching)==2
        assert all(n['message']==expected for n in matching)
    for n in notes:
        assert all(secret not in n['message'] for secret in ['876543','654321','secret','Private merchant'])
