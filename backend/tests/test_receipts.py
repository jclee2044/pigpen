import json
from uuid import uuid4
from datetime import datetime,timezone,timedelta
from sqlalchemy import select,update
import pytest
from conftest import operation,submit
from test_attachments_push import png
from pigpen.database import Database
from pigpen import schema as s
from pigpen.receipt_parser import parse_receipt,expiry
from pigpen.receipt_worker import process_once,cleanup
from pigpen.recovery import backup,restore,validate_backup
from pigpen.app import create_app
from fastapi.testclient import TestClient


def lines(*texts):return [{'text':t,'score':.99} for t in texts]

def scan(client,actor,identifier=None):
    return client.post('/api/v1/receipt-scans',data={'operation_id':identifier or str(uuid4()),'actor_id':actor,'client_time':'2026-11-09T12:00:00Z'},files={'file':('receipt.png',png(),'image/png')})

def ready(client,users,settings):
    r=scan(client,users[0]['id']);assert r.status_code==202,r.text
    db=Database(settings)
    assert process_once(db,lambda p:parse_receipt(lines('MARKET','Apples 3.50','TOTAL 3.50')))
    return client.get('/api/v1/receipt-scans/'+r.json()['id']).json()

def confirmation(client,users,row,**extra):
    category=next(x for x in client.get('/api/v1/categories').json()['items'] if x['kind']=='expense')
    return operation('receipt.confirm',{'scan_id':row['id'],'expected_revision':row['revision'],'purchase':{
        'item':'Apples','amount_minor':350,'category_id':category['id'],'transaction_date':'2026-11-09','merchant':'MARKET','description':'Apples — $3.50'},**extra},users[0]['id'])

def test_parser_totals_and_abstention():
    out=parse_receipt(lines('MARKET','2026-11-09','Apples 3.50','Bread 4.00','Subtotal 7.50','Tax 0.45','TOTAL 7.95','Cash 20.00','Change 12.05'))
    assert out['amount_minor']==795 and out['merchant']=='MARKET' and len(out['line_items'])==2
    assert out['transaction_date']=='2026-11-09'
    assert parse_receipt(lines('Subtotal 4.00','Cash 10.00'))['amount_minor'] is None
    assert parse_receipt(lines('TOTAL 4.00','TOTAL 5.00'))['amount_minor'] is None
    assert parse_receipt(lines('TOTAL 4.00','Tip ______'))['amount_minor'] is None
    assert parse_receipt(lines('TOTAL EUR 4.00'))['amount_minor'] is None
    assert parse_receipt([{'text':'TOTAL 4.00','score':.7}])['amount_minor'] is None
    assert expiry('2026-11-30T12:00:00+00:00')=='2027-02-28T12:00:00+00:00'
    assert expiry('2023-11-30T12:00:00+00:00')=='2024-02-29T12:00:00+00:00'

def test_atomic_confirmation_replay_duplicates_and_actor(client,users,settings):
    row=ready(client,users,settings)
    assert client.get('/api/v1/purchases').json()['items']==[]
    op=confirmation(client,users,row)
    wrong={**op,'actor_id':users[1]['id']}
    assert client.post('/api/v1/operations',json=wrong).status_code==403
    first=client.post('/api/v1/operations',json=op);assert first.status_code==200,first.text
    assert client.post('/api/v1/operations',json=op).json()==first.json()
    assert client.post('/api/v1/operations',json={**op,'operation_id':str(uuid4()),'entity_id':str(uuid4())}).status_code==409
    purchase=first.json()['result'];assert purchase['amount_minor']==350
    attachments=client.get('/api/v1/purchases/'+purchase['id']+'/attachments').json()['items']
    assert len(attachments)==1 and attachments[0]['receipt_scan_id']==row['id']
    assert client.get('/api/v1/attachments/'+attachments[0]['id']+'/content').status_code==200
    row2=ready(client,users,settings);op2=confirmation(client,users,row2)
    assert client.post('/api/v1/operations',json=op2).json()['error']['code']=='receipt_duplicate'
    op2['data']['allow_duplicate']=True
    assert client.post('/api/v1/operations',json=op2).status_code==200
    assert len(client.get('/api/v1/purchases').json()['items'])==2

def test_upload_replay_bad_images_and_cancel(client,users,settings):
    identifier=str(uuid4());r=scan(client,users[0]['id'],identifier)
    assert scan(client,users[0]['id'],identifier).json()==r.json()
    assert scan(client,users[1]['id'],identifier).status_code==409
    assert client.post('/api/v1/receipt-scans',data={'operation_id':str(uuid4()),'actor_id':users[0]['id'],'client_time':'2026-11-09T12:00:00Z'},files={'file':('a.jpg',b'broken','image/jpeg')}).status_code==422
    row=r.json();submit(client,'receipt.cancel',{'expected_revision':row['revision']},users[0]['id'],row['id'])
    assert not process_once(Database(settings),lambda p:None)
    assert client.get('/api/v1/purchases').json()['items']==[]

def test_worker_failure_retry_lease_and_cancellation(client,users,settings):
    row=scan(client,users[0]['id']).json();db=Database(settings)
    def fail(path):raise RuntimeError('private data must not leak')
    assert process_once(db,fail)
    row=client.get('/api/v1/receipt-scans/'+row['id']).json();assert row['status']=='failed' and 'private' not in row['error']
    submit(client,'receipt.retry',{'expected_revision':row['revision']},users[0]['id'],row['id'])
    with db.transaction(write=True) as c:c.execute(update(s.receipt_scans).values(status='processing',lease_until='2000-01-01',lease_token='old'))
    def cancel(path):
        current=client.get('/api/v1/receipt-scans/'+row['id']).json()
        submit(client,'receipt.cancel',{'expected_revision':current['revision']},users[0]['id'],row['id'])
        return parse_receipt(lines('TOTAL 2.00'))
    assert process_once(db,cancel)
    assert client.get('/api/v1/receipt-scans/'+row['id']).json()['status']=='canceled'

def test_expiry_override_shared_images_backup_restore(client,users,settings,tmp_path):
    row=ready(client,users,settings)
    purchase=client.post('/api/v1/operations',json=confirmation(client,users,row)).json()['result']
    db=Database(settings)
    photo=client.get('/api/v1/purchases/'+purchase['id']+'/attachments').json()['items'][0]
    kept=ready(client,users,settings)
    kept=submit(client,'receipt.retention',{'expected_revision':kept['revision'],'keep_indefinitely':True},users[0]['id'],kept['id'])
    snapshot=backup(settings,tmp_path/'before');validate_backup(snapshot)
    stamp=(datetime.now(timezone.utc)+timedelta(days=100)).isoformat()
    cleanup(db,stamp)
    assert client.get('/api/v1/attachments/'+photo['id']+'/content').status_code==410
    assert list(settings.uploads_dir.glob('*.png')) # same bytes protected by retained draft
    kept=submit(client,'receipt.retention',{'expected_revision':kept['revision'],'keep_indefinitely':False},users[0]['id'],kept['id'])
    cleanup(db,stamp);assert not list(settings.uploads_dir.glob('*.png'))
    cleanup(db,stamp) # idempotent
    assert client.get('/api/v1/purchases').json()['items'][0]['amount_minor']==350
    after=backup(settings,tmp_path/'after');assert not (after/'uploads').exists()
    recovered=restore(after,tmp_path/'restored','test')
    with TestClient(create_app(recovered)) as restored:
        assert restored.get('/api/v1/attachments/'+photo['id']+'/content').status_code==410
        assert len(restored.get('/api/v1/purchases').json()['items'])==1
    validate_backup(snapshot) # historical snapshot is intact

def test_confirmation_rolls_back_invalid_category_and_preserves_notifications(client,users,settings):
    row=ready(client,users,settings);op=confirmation(client,users,row);db=Database(settings)
    bad={**op,'data':{**op['data'],'purchase':{**op['data']['purchase'],'category_id':str(uuid4())}}}
    assert client.post('/api/v1/operations',json=bad).status_code==404
    assert client.get('/api/v1/purchases').json()['items']==[]
    assert client.get('/api/v1/receipt-scans/'+row['id']).json()['status']=='ready'
    assert client.post('/api/v1/operations',json=op).status_code==200
    with db.transaction() as c:
        original=list(c.execute(select(s.notifications.c.id)))
    assert client.post('/api/v1/operations',json=op).status_code==200
    with db.transaction() as c:assert list(c.execute(select(s.notifications.c.id)))==original

def test_concurrent_confirmation_and_stale_override(client,users,settings):
    from concurrent.futures import ThreadPoolExecutor
    row=ready(client,users,settings)
    op1=confirmation(client,users,row);op2=confirmation(client,users,row)
    with ThreadPoolExecutor(2) as pool:
        responses=list(pool.map(lambda op:client.post('/api/v1/operations',json=op),[op1,op2]))
    assert sorted(r.status_code for r in responses)==[200,409]
    assert len(client.get('/api/v1/purchases').json()['items'])==1
    stale=operation('receipt.retention',{'expected_revision':row['revision'],'keep_indefinitely':True},users[0]['id'],row['id'])
    assert client.post('/api/v1/operations',json=stale).status_code==409

def test_cleanup_does_not_delete_manual_attachment_shared_bytes(client,users,settings):
    row=ready(client,users,settings);db=Database(settings)
    purchase=client.post('/api/v1/operations',json=confirmation(client,users,row)).json()['result']
    response=client.post('/api/v1/purchases/'+purchase['id']+'/attachments',data={'operation_id':str(uuid4()),'actor_id':users[0]['id'],'client_time':'2026-11-09T12:00:00Z'},files={'file':('bank.png',png(),'image/png')})
    assert response.status_code==200
    cleanup(db,(datetime.now(timezone.utc)+timedelta(days=100)).isoformat())
    assert client.get('/api/v1/attachments/'+response.json()['result']['id']+'/content').status_code==200

def test_expired_upload_replay_does_not_recreate_photo(client,users,settings):
    actor=users[0]['id'];identifier=str(uuid4());assert scan(client,actor,identifier).status_code==202
    cleanup(Database(settings),(datetime.now(timezone.utc)+timedelta(days=100)).isoformat())
    assert not list(settings.uploads_dir.glob('*.png'))
    assert scan(client,actor,identifier).status_code==202
    assert not list(settings.uploads_dir.glob('*.png'))

def test_queue_cap_and_single_processing_lease(client,users,settings):
    for _ in range(10):assert scan(client,users[0]['id']).status_code==202
    assert scan(client,users[0]['id']).status_code==429
    db=Database(settings)
    with db.transaction(write=True) as c:
        identifier=c.execute(select(s.receipt_scans.c.id).limit(1)).scalar()
        c.execute(update(s.receipt_scans).where(s.receipt_scans.c.id==identifier).values(status='processing',lease_until=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()))
    assert not process_once(db,lambda _:None)


def test_uncertain_receipt_boundary_fails_without_purchase(client, users, settings):
    from pigpen.receipt_worker import ReceiptBoundaryError
    row = scan(client, users[0]['id']).json()
    def uncertain(_path):
        raise ReceiptBoundaryError()
    assert process_once(Database(settings), uncertain)
    result = client.get('/api/v1/receipt-scans/' + row['id']).json()
    assert result['status'] == 'failed'
    assert 'Retake' in result['error']
    assert result['suggestions'] is None
    assert not client.get('/api/v1/purchases').json()['items']
