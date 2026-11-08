from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select, insert
from . import schema as s
from .records import get, expect, now
from .errors import DomainError


def notification_message(c,op,kind,resource,target):
    """Snapshot only explicitly approved preview fields, never financial data."""
    def clean(value,limit):
        return ' '.join(str(value).split())[:limit]
    actor=c.execute(select(s.users.c.name).where(s.users.c.id==op['actor_id'])).scalar()
    actor=clean(actor or 'Someone',80)
    fields={'wishlist-items':(s.wishlist_items,'name'),
            'approval-requests':(s.approval_requests,'item'),
            'purchases':(s.purchases,'item'),'categories':(s.categories,'name')}
    label=''
    if resource in fields:
        table,column=fields[resource]
        label=clean(c.execute(select(table.c[column]).where(table.c.id==target)).scalar() or '',140)
    item=f'"{label}"' if label else 'an item'
    messages={
        'wishlist.created':f'{actor} just added {item} to the wish list',
        'purchase.created':f'{actor} added a purchase: {item}',
        'request.created':f'{actor} submitted {item} for approval',
        'request.revised':f'{actor} updated the approval request for {item}',
        'request.canceled':f'{actor} canceled the approval request for {item}',
        'approval.on':f'{actor} approved {item}',
        'approval.off':f'{actor} removed approval for {item}',
        'comment.created':f'{actor} commented on {item}',
        'budget.reached':f'{actor} recorded spending that reached the {label or "category"} budget',
        'budget.exceeded':f'{actor} recorded spending that exceeded the {label or "category"} budget',
    }
    return messages.get(kind,f'{actor} made a household update')


class NotificationServices:
    def notify(self,c,op,kind,resource,target,event_key=None,recipients=None):
        recipients=recipients if recipients is not None else [r for r in c.execute(select(s.users.c.id).where(s.users.c.active==True)).scalars()]
        event_key=event_key or op['operation_id']+':'+kind
        message=notification_message(c,op,kind,resource,target)
        for recipient in recipients:
            if recipient == op['actor_id'] and not kind.startswith('budget.'):
                continue
            existing=c.execute(select(s.notifications.c.id).where(s.notifications.c.recipient_id==recipient,s.notifications.c.event_key==event_key)).first()
            if existing:
                continue
            notification=self.save(c,s.notifications,dict(id=str(uuid5(NAMESPACE_URL,recipient+'/'+event_key)),recipient_id=recipient,
                event_key=event_key,kind=kind,target_resource=resource,target_id=target,read_at=None,message=message))
            c.execute(insert(s.outbox).values(id=notification['id'],notification_id=notification['id'],recipient_id=recipient,
                attempts=0,next_attempt=now(),delivered_at=None,lease_until=None,lease_token=None,last_error=None))

    def do_notification_read(self,c,op):
        row=get(c,s.notifications,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['recipient_id'] != op['actor_id']:
            raise DomainError('actor','Only the recipient can mark a notification read',403)
        if row['read_at']:
            return row
        return self.save(c,s.notifications,{'read_at':now()},row)
