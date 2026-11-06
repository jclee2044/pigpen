"""Installation binding and one-shot durable Web Push delivery."""
import base64
from datetime import datetime, timedelta, timezone
import json
from urllib.parse import urlparse
from uuid import uuid4, uuid5, NAMESPACE_URL
from sqlalchemy import select, insert, update, or_
from . import schema as s
from .records import get, expect, now
from .errors import DomainError

PUSH_HOSTS=('fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com')


def validate_subscription(data):
    url=urlparse(data['endpoint']);host=url.hostname or ''
    if url.scheme!='https' or url.username or url.password or url.port not in (None,443) or not (
        host in PUSH_HOSTS or host.endswith('.push.services.mozilla.com') or host.endswith('.notify.windows.com')):
        raise DomainError('push_endpoint','Use a supported browser HTTPS push endpoint')
    try:
        public=base64.urlsafe_b64decode(data['p256dh']+'='*(-len(data['p256dh'])%4))
        secret=base64.urlsafe_b64decode(data['auth']+'='*(-len(data['auth'])%4))
        if len(public)!=65 or public[0]!=4 or len(secret)!=16:
            raise ValueError()
    except (ValueError,TypeError):
        raise DomainError('push_keys','Invalid browser push subscription keys') from None


class PushServices:
    def do_installation_select(self,c,op):
        row=c.execute(select(s.installations).where(s.installations.c.id==op['entity_id'])).mappings().first()
        if row:
            row=dict(row);expect(row,op['data']['expected_revision'])
        elif op['data']['expected_revision']:
            raise DomainError('revision_conflict','New installations require revision 0',409)
        return self.save(c,s.installations,dict(id=op['entity_id'],user_id=op['actor_id']),row)

    def do_subscription_set(self,c,op):
        data=dict(op['data']);installation=get(c,s.installations,data['installation_id'])
        if installation['user_id']!=op['actor_id']:
            raise DomainError('actor','Select this profile on the installation first',409)
        validate_subscription(data)
        row=c.execute(select(s.subscriptions).where(s.subscriptions.c.installation_id==installation['id'])).mappings().first()
        revision=data.pop('expected_revision')
        if row:
            row=dict(row)
            if row['id']!=op['entity_id']:
                raise DomainError('subscription_id','Use the existing subscription ID',409)
            expect(row,revision)
        elif revision:
            raise DomainError('revision_conflict','New subscriptions require revision 0',409)
        result=self.save(c,s.subscriptions,dict(id=op['entity_id'],**data,active=True),row)
        return {k:result[k] for k in ['id','revision','installation_id','active']}

    def do_subscription_disable(self,c,op):
        row=get(c,s.subscriptions,op['entity_id']);expect(row,op['data']['expected_revision'])
        if get(c,s.installations,row['installation_id'])['user_id']!=op['actor_id']:
            raise DomainError('actor','Subscription belongs to another selected profile',403)
        result=self.save(c,s.subscriptions,{'active':False},row)
        return {k:result[k] for k in ['id','revision','installation_id','active']}


def send_webpush(settings,subscription,payload):
    from pywebpush import webpush, WebPushException
    from requests import Session
    class NoRedirectSession(Session):
        def request(self,*args,**kwargs):
            kwargs['allow_redirects']=False
            return super().request(*args,**kwargs)
    try:
        with NoRedirectSession() as session:
            response=webpush(subscription_info={'endpoint':subscription['endpoint'],
                'keys':{'p256dh':subscription['p256dh'],'auth':subscription['auth']}},data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,vapid_claims={'sub':settings.vapid_subject},
                timeout=10,requests_session=session)
            return response.status_code
    except WebPushException as exc:
        return exc.response.status_code if exc.response is not None else 503
    except Exception:
        return 503


def deliver_once(db,sender=None):
    if sender is None:
        if not db.settings.vapid_private_key or not db.settings.vapid_subject:
            raise ValueError('Configure private VAPID credentials before push delivery')
        sender=lambda subscription,payload:send_webpush(db.settings,subscription,payload)
    timestamp=now();token=str(uuid4())
    with db.transaction(write=True) as c:
        job=c.execute(select(s.outbox).where(s.outbox.c.delivered_at.is_(None),s.outbox.c.next_attempt<=timestamp,
            or_(s.outbox.c.lease_until.is_(None),s.outbox.c.lease_until<timestamp)).order_by(s.outbox.c.next_attempt).limit(1)).mappings().first()
        if not job:
            return False
        job=dict(job)
        c.execute(update(s.outbox).where(s.outbox.c.id==job['id']).values(lease_token=token,
            lease_until=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()))
    with db.transaction() as c:
        recipients=[dict(r) for r in c.execute(select(s.subscriptions,s.installations.c.revision.label('binding_revision'))
            .join(s.installations,s.subscriptions.c.installation_id==s.installations.c.id)
            .join(s.users,s.installations.c.user_id==s.users.c.id)
            .where(s.installations.c.user_id==job['recipient_id'],s.subscriptions.c.active==True,s.users.c.active==True)).mappings()]
    failed=False
    for subscription in recipients:
        delivery_id=str(uuid5(NAMESPACE_URL,job['notification_id']+'/'+subscription['id']+'/'+str(subscription['binding_revision'])))
        # Resolve binding immediately before delivery; successful devices are not resent on retry.
        with db.transaction() as c:
            if c.execute(select(s.push_deliveries.c.id).where(s.push_deliveries.c.id==delivery_id)).first():
                continue
            binding=get(c,s.installations,subscription['installation_id'])
            current=get(c,s.subscriptions,subscription['id'])
            if binding['user_id']!=job['recipient_id'] or binding['revision']!=subscription['binding_revision'] or current['revision']!=subscription['revision'] or not current['active']:
                continue
        try:
            status=sender(subscription,{'notification_id':job['notification_id'],'url':'/notifications','tag':job['notification_id']})
        except Exception:
            status=503
        with db.transaction(write=True) as c:
            if 200<=status<300:
                c.execute(insert(s.push_deliveries).values(id=delivery_id,notification_id=job['notification_id'],
                    subscription_id=subscription['id'],binding_revision=subscription['binding_revision'],delivered_at=now()))
            elif status in {404,410}:
                c.execute(update(s.subscriptions).where(s.subscriptions.c.id==subscription['id'],s.subscriptions.c.revision==subscription['revision'])
                    .values(active=False,revision=subscription['revision']+1,updated_at=now()))
            else:
                failed=True
    with db.transaction(write=True) as c:
        attempts=job['attempts']+1
        c.execute(update(s.outbox).where(s.outbox.c.id==job['id'],s.outbox.c.lease_token==token).values(
            attempts=attempts,lease_until=None,lease_token=None,last_error='temporary_delivery_failure' if failed else None,
            next_attempt=(datetime.now(timezone.utc)+timedelta(seconds=min(604800,30*2**min(attempts,15)))).isoformat(),
            delivered_at=None if failed else now()))
    return True
