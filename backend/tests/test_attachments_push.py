import base64
from io import BytesIO
from uuid import uuid4
from PIL import Image
from sqlalchemy import select, update
from conftest import operation, submit
from pigpen import schema as s
from pigpen.database import Database
from pigpen.push import deliver_once


def png():
    output=BytesIO();Image.new('RGB',(4,4),'pink').save(output,'PNG');return output.getvalue()


def purchase(client,actor):
    category=next(c for c in client.get('/api/v1/categories').json()['items'] if c['name']=='Food')
    return submit(client,'purchase.create',dict(item='Receipt',amount_minor=100,category_id=category['id'],transaction_date='2026-11-06'),actor)


def test_validated_upload_retry_download_and_delete(client,users,settings):
    actor=users[0]['id'];p=purchase(client,actor)
    form=dict(operation_id=str(uuid4()),actor_id=actor,client_time='2026-11-06T12:00:00Z')
    url=f"/api/v1/purchases/{p['id']}/attachments"
    first=client.post(url,data=form,files={'file':('../../receipt.png',png(),'image/png')})
    assert first.status_code==200,first.text
    record=first.json()['result'];assert record['filename']=='receipt.png'
    assert client.post(url,data=form,files={'file':('../../receipt.png',png(),'image/png')}).json()==first.json()
    assert len(list(settings.uploads_dir.iterdir()))==1
    content=client.get(f"/api/v1/attachments/{record['id']}/content")
    assert content.content==png() and content.headers['cache-control']=='no-store'
    response=client.delete(f"/api/v1/attachments/{record['id']}",params=dict(operation_id=str(uuid4()),actor_id=actor,
        expected_revision=1,client_time='2026-11-06T12:00:00Z'))
    assert response.status_code==200
    assert client.get(url).json()['items']==[]
    assert client.get(f"/api/v1/attachments/{record['id']}/content").status_code==404
    assert len(list(settings.uploads_dir.iterdir()))==1


def test_fake_or_mismatched_images_are_rejected(client,users,settings):
    actor=users[0]['id'];p=purchase(client,actor);url=f"/api/v1/purchases/{p['id']}/attachments"
    form=dict(operation_id=str(uuid4()),actor_id=actor,client_time='2026-11-06T12:00:00Z')
    for data,media in [(b'not an image','image/png'),(png(),'image/jpeg')]:
        assert client.post(url,data=form,files={'file':('receipt.png',data,media)}).status_code==422
    assert not settings.uploads_dir.exists()


def subscription(client,actor,endpoint='https://fcm.googleapis.com/fcm/send/synthetic'):
    install=submit(client,'installation.select',{},actor)
    keys=dict(p256dh=base64.urlsafe_b64encode(b'\x04'+b'X'*64).decode().rstrip('='),auth=base64.urlsafe_b64encode(b'A'*16).decode().rstrip('='))
    sub=submit(client,'subscription.set',dict(installation_id=install['id'],endpoint=endpoint,**keys),actor)
    return install,sub


def test_push_rebinding_prevents_old_profile_delivery(client,users,settings):
    a,b,c=[x['id'] for x in users]
    install,sub=subscription(client,b)
    submit(client,'wishlist.create',dict(name='Wish',price_minor=100),a)
    submit(client,'installation.select',dict(expected_revision=1),c,install['id'])
    calls=[]
    while deliver_once(Database(settings),lambda sub,payload:calls.append(payload) or 200):pass
    assert len(calls)==1 # the C notification is delivered; the queued B notification is skipped.
    with Database(settings).transaction() as conn:
        delivery=conn.execute(select(s.push_deliveries)).mappings().one()
        note=conn.execute(select(s.notifications).where(s.notifications.c.id==delivery['notification_id'])).mappings().one()
        assert note['recipient_id']==c
    snapshot=client.get('/api/v1/sync/snapshot').json()
    assert 'subscriptions' not in snapshot['records']
    assert 'endpoint' not in str(client.get('/api/v1/installations/'+install['id']).json())


def test_push_retry_and_expiration(client,users,settings):
    a,b,c=[x['id'] for x in users];install,sub=subscription(client,b)
    submit(client,'wishlist.create',dict(name='Wish',price_minor=100),a)
    db=Database(settings)
    assert deliver_once(db,lambda sub,payload:503)
    with db.transaction(write=True) as conn:
        pending=conn.execute(select(s.outbox).where(s.outbox.c.last_error.is_not(None))).mappings().one()
        assert pending['attempts']==1 and pending['delivered_at'] is None
        conn.execute(update(s.outbox).where(s.outbox.c.id==pending['id']).values(next_attempt='2000'))
    assert deliver_once(db,lambda sub,payload:410)
    with db.transaction() as conn:
        assert conn.execute(select(s.subscriptions.c.active)).scalar() is False


def test_unsafe_push_endpoint_rejected(client,users):
    actor=users[0]['id'];installation=submit(client,'installation.select',{},actor)
    op=operation('subscription.set',dict(installation_id=installation['id'],endpoint='https://127.0.0.1/private',p256dh='x',auth='x'),actor)
    response=client.post('/api/v1/operations',json=op)
    assert response.status_code==422
    assert 'private' not in str(response.json())


def test_upload_requires_timezone_aware_timestamp_before_storing(client,users,settings):
    actor=users[0]['id'];p=purchase(client,actor)
    form=dict(operation_id=str(uuid4()),actor_id=actor,client_time='2026-11-06T12:00:00')
    result=client.post(f"/api/v1/purchases/{p['id']}/attachments",data=form,files={'file':('image.png',png(),'image/png')})
    assert result.status_code==422
    assert not settings.uploads_dir.exists()
