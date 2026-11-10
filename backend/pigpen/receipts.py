"""Receipt jobs and reviewed purchase creation. No OCR runs in a transaction."""
from hashlib import sha256
import json
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select, func
from . import schema as s
from .records import get, expect, now
from .errors import DomainError
from .receipt_parser import expiry
from .attachments import attachment_path, store_image


def expired(row, stamp=None):
    return bool(row.get('expired_at') or (row.get('expires_at') and not row.get('keep_indefinitely') and row['expires_at'] <= (stamp or now())))


def public_scan(row):
    return {k:v for k,v in row.items() if k not in {'storage_key','checksum','payload_hash','lease_token','lease_until','household_id','deleted'}}


def require_image(row):
    if expired(row):
        raise DomainError('receipt_expired','This receipt photo has expired; the purchase details are preserved.',410)


class ReceiptServices:
    def create_scan(self, identifier, actor, client_time, metadata, image_data):
        digest=sha256(json.dumps({'actor':actor,'time':client_time,'image':metadata},sort_keys=True).encode()).hexdigest()
        with self.db.transaction(write=True) as c:
            get(c,s.users,actor,active=True)
            prior=c.execute(select(s.receipt_scans).where(s.receipt_scans.c.id==identifier)).mappings().first()
            if prior:
                if prior['payload_hash']!=digest:
                    raise DomainError('operation_conflict','Scan ID already used with different content',409)
                return public_scan(dict(prior))
            count=c.execute(select(func.count()).select_from(s.receipt_scans).where(s.receipt_scans.c.status.in_(['queued','processing']))).scalar()
            if count>=10:
                raise DomainError('receipt_busy','Receipt queue is full. Retry shortly.',429)
            store_image(self.db.settings,image_data,metadata["media_type"],metadata["filename"])
            stamp=now()
            row=self.save(c,s.receipt_scans,dict(id=identifier,actor_id=actor,payload_hash=digest,status='queued',
                **metadata,suggestions=None,error=None,attempts=0,lease_until=None,lease_token=None,
                expires_at=expiry(stamp),keep_indefinitely=False,expired_at=None,purchase_id=None,created_at=stamp))
            return public_scan(row)

    def scan_for_actor(self,c,op):
        row=get(c,s.receipt_scans,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['actor_id']!=op['actor_id'] and row['status']!='confirmed':
            raise DomainError('actor','Switch to the profile that scanned this receipt.',403)
        return row

    def do_receipt_cancel(self,c,op):
        row=self.scan_for_actor(c,op)
        if row['status']=='confirmed':
            raise DomainError('receipt_state','This receipt already belongs to a purchase.',409)
        return public_scan(self.save(c,s.receipt_scans,{'status':'canceled','lease_token':None,'lease_until':None},row))

    def do_receipt_retry(self,c,op):
        row=self.scan_for_actor(c,op);require_image(row)
        if row['status']!='failed':
            raise DomainError('receipt_state','Only failed scans can be retried.',409)
        if c.execute(select(func.count()).select_from(s.receipt_scans).where(s.receipt_scans.c.status.in_(['queued','processing']))).scalar()>=10:
            raise DomainError('receipt_busy','Receipt queue is full. Retry shortly.',429)
        return public_scan(self.save(c,s.receipt_scans,{'status':'queued','error':None,'attempts':0},row))

    def do_receipt_retention(self,c,op):
        row=self.scan_for_actor(c,op)
        if row['expired_at']:
            raise DomainError('receipt_expired','Deleted photos cannot be restored.',410)
        keep=op['data']['keep_indefinitely']
        row=self.save(c,s.receipt_scans,{'keep_indefinitely':keep},row)
        for image in c.execute(select(s.attachments).where(s.attachments.c.receipt_scan_id==row['id'])).mappings():
            self.save(c,s.attachments,{'keep_indefinitely':keep},dict(image))
        return public_scan(row)

    def do_receipt_confirm(self,c,op):
        data=op['data'];scan=get(c,s.receipt_scans,data['scan_id'])
        if scan['status']=='confirmed':
            raise DomainError('receipt_confirmed','This scan already created a purchase.',409,{'purchase_id':scan['purchase_id']})
        expect(scan,data['expected_revision']);require_image(scan)
        if scan['actor_id']!=op['actor_id']:
            raise DomainError('actor','Switch to the profile that scanned this receipt.',403)
        if scan['status']!='ready':
            raise DomainError('receipt_state','Wait for the scan to finish before saving.',409)
        values=data['purchase']
        duplicates=set(c.execute(select(s.attachments.c.purchase_id).where(s.attachments.c.checksum==scan['checksum'])).scalars())
        if values['merchant']:
            duplicates.update(c.execute(select(s.purchases.c.id).where(
                func.lower(s.purchases.c.merchant)==values['merchant'].lower(),
                s.purchases.c.transaction_date==values['transaction_date'],s.purchases.c.amount_minor==values['amount_minor'])).scalars())
        if duplicates and not data['allow_duplicate']:
            raise DomainError('receipt_duplicate','A matching receipt or purchase already exists. Review it before saving another.',409,{'purchase_ids':sorted(duplicates)})
        path=attachment_path(self.db.settings,scan)
        if sha256(path.read_bytes()).hexdigest()!=scan['checksum']:
            raise DomainError('storage','Receipt image failed its integrity check.',503)
        result=self.do_purchase_create(c,{**op,'data':values})
        fields={k:scan[k] for k in ['storage_key','filename','media_type','byte_size','checksum','expires_at']}
        self.save(c,s.attachments,dict(id=str(uuid5(NAMESPACE_URL,scan['id']+'/attachment')),purchase_id=result['id'],
            uploader_id=op['actor_id'],**fields,receipt_scan_id=scan['id'],keep_indefinitely=data['keep_indefinitely'],expired_at=None))
        self.save(c,s.receipt_scans,{'status':'confirmed','purchase_id':result['id'],'keep_indefinitely':data['keep_indefinitely']},scan)
        return result
