"""Bounded local OCR jobs and restart-safe photo expiry."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4,uuid5,NAMESPACE_URL
import json, os, subprocess
from sqlalchemy import select, or_, insert
from . import schema as s
from .records import now, get
from .service import Service
from .receipts import expired
from .receipt_parser import parse_receipt
from .attachments import attachment_path
from .image_lock import image_lock

ROOT=Path(__file__).resolve().parents[2]


class ReceiptBoundaryError(ValueError):
    pass


def extract(path):
    run=subprocess.run([str(ROOT/'backend/.ocr-venv/bin/python'),str(ROOT/'tools/receipt_ocr.py'),str(path)],
        capture_output=True,text=True,timeout=45,env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1'})
    if run.returncode:
        raise RuntimeError('OCR process failed')
    result=json.loads(run.stdout)
    if isinstance(result,dict) and result.get('error')=='receipt_boundary':
        raise ReceiptBoundaryError()
    return parse_receipt(result)


def process_once(db, extractor=extract):
    service=Service(db);stamp=now();token=str(uuid4())
    with db.transaction(write=True) as c:
        if c.execute(select(s.receipt_scans.c.id).where(s.receipt_scans.c.status=='processing',s.receipt_scans.c.lease_until>=stamp)).first():
            return False
        candidate=c.execute(select(s.receipt_scans).where(or_(s.receipt_scans.c.status=='queued',
            (s.receipt_scans.c.status=='processing') & (s.receipt_scans.c.lease_until<stamp))).order_by(s.receipt_scans.c.created_at).limit(1)).mappings().first()
        if not candidate:return False
        row=dict(candidate)
        if expired(row) or row['attempts']>=3:
            service.save(c,s.receipt_scans,{'status':'failed','error':'Receipt expired or scan attempts exhausted.','lease_token':None,'lease_until':None},row)
            return True
        row=service.save(c,s.receipt_scans,{'status':'processing','attempts':row['attempts']+1,'lease_token':token,
            'lease_until':(datetime.now(timezone.utc)+timedelta(seconds=90)).isoformat()},row)
    try:
        result=extractor(attachment_path(db.settings,row))
        values={'status':'ready','suggestions':result,'error':None}
    except ReceiptBoundaryError:
        values={'status':'failed','error':'Could not isolate the receipt. Retake with only the receipt in view, against a plain dark background.'}
    except Exception:
        # Never log subprocess output or receipt payloads.
        values={'status':'failed','error':'Could not read this receipt. Retry, take a clearer photo, or enter it manually.'}
    with db.transaction(write=True) as c:
        current=get(c,s.receipt_scans,row['id'])
        if current['status']=='processing' and current['lease_token']==token:
            service.save(c,s.receipt_scans,{**values,'lease_token':None,'lease_until':None},current)
    return True


def cleanup(db, stamp=None):
    stamp=stamp or now();service=Service(db)
    with image_lock(db.settings):
        with db.transaction(write=True) as c:
            for raw in c.execute(select(s.receipt_scans).where(s.receipt_scans.c.expired_at.is_(None),
                    s.receipt_scans.c.keep_indefinitely==False,s.receipt_scans.c.expires_at<=stamp)).mappings():
                row=dict(raw)
                if row['status']=='processing' and row['lease_until'] and row['lease_until']>stamp:continue
                service.save(c,s.receipt_scans,{'expired_at':stamp,'status':row['status'] if row['status'] in ('confirmed','canceled') else 'failed',
                    'error':row['error'] if row['status']=='confirmed' else 'Receipt photo expired.', 'lease_token':None,'lease_until':None},row)
                c.execute(insert(s.audit_events).values(operation_id=str(uuid5(NAMESPACE_URL,row['id']+'/expiry')),actor_id=None,kind='receipt.expire',target_id=row['id'],client_time=stamp,server_time=stamp))
                for raw_image in c.execute(select(s.attachments).where(s.attachments.c.receipt_scan_id==row['id'])).mappings():
                    service.save(c,s.attachments,{'expired_at':stamp},dict(raw_image))
            # Expired metadata commits first. A crash before unlink is retried next run.
        with db.transaction() as c:
            expired_rows=[dict(r) for r in c.execute(select(s.receipt_scans).where(s.receipt_scans.c.expired_at.is_not(None))).mappings()]
            protected={r['storage_key'] for r in c.execute(select(s.attachments)).mappings() if not r['expired_at']}
            protected.update(r['storage_key'] for r in c.execute(select(s.receipt_scans)).mappings() if not r['expired_at'])
        for row in expired_rows:
            if row['storage_key'] in protected:continue
            try:path=attachment_path(db.settings,row)
            except Exception:continue
            path.unlink(missing_ok=True)


def loop(db, stop):
    import time
    last_cleanup=0
    while not stop.is_set():
        try:
            if time.monotonic()-last_cleanup>86400 or not last_cleanup:
                cleanup(db);last_cleanup=time.monotonic()
            worked=process_once(db)
        except Exception:
            worked=False
        stop.wait(.2 if worked else 2)
