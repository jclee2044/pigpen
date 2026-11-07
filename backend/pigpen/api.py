from fastapi import APIRouter, Query, Form, File, UploadFile
from fastapi.responses import FileResponse
from uuid import UUID, uuid5, NAMESPACE_URL
from sqlalchemy import select
from .contracts import Operation, Model, AttachmentOperation, AttachmentDeleteOperation
from pydantic import Field, AwareDatetime
from . import sync
from .domain import month_bounds
from .attachments import MAX_UPLOAD, store_image, attachment_path
from .service import Service, get, avatar_options
from . import schema as s
from .errors import DomainError


class PushBatch(Model):
    operations: list[Operation] = Field(min_length=1, max_length=100)


def router(db):
    routes = APIRouter(prefix='/api/v1')
    service = Service(db)

    @routes.get('/push-config')
    def push_configuration():
        from .push import push_config
        return push_config(db.settings)

    @routes.post('/operations')
    def execute(operation: Operation):
        return service.execute(operation)

    @routes.post('/sync/push')
    def sync_push(batch: PushBatch):
        return sync.push(service, batch.operations)

    @routes.get('/sync/pull')
    def sync_pull(cursor: int = Query(0,ge=0), limit: int = Query(100,ge=1,le=100)):
        return sync.pull(db,cursor,limit)

    @routes.get('/sync/snapshot')
    def sync_snapshot():
        return sync.snapshot(db)

    @routes.post('/purchases/{purchase_id}/attachments')
    def upload(purchase_id: UUID, operation_id: UUID = Form(...), actor_id: UUID = Form(...),
               client_time: AwareDatetime = Form(...), file: UploadFile = File(...)):
        with db.transaction() as c:
            get(c,s.purchases,purchase_id)
            get(c,s.users,actor_id,active=True)
        try:
            data=file.file.read(MAX_UPLOAD+1)
        finally:
            file.file.close()
        metadata=store_image(db.settings,data,file.content_type,file.filename)
        operation=AttachmentOperation(operation_id=operation_id,entity_id=uuid5(NAMESPACE_URL,str(purchase_id)+'/'+str(operation_id)),
            actor_id=actor_id,client_time=client_time,data={'purchase_id':purchase_id,**metadata})
        return service.execute(operation)

    @routes.get('/purchases/{purchase_id}/attachments')
    def attachment_list(purchase_id: UUID):
        with db.transaction() as c:
            get(c,s.purchases,purchase_id)
            return {'items':[dict(r) for r in c.execute(select(s.attachments).where(s.attachments.c.purchase_id==str(purchase_id),s.attachments.c.deleted==False)).mappings()]}

    @routes.get('/attachments/{identifier}/content')
    def attachment_content(identifier: UUID):
        with db.transaction() as c:
            record=get(c,s.attachments,identifier)
            get(c,s.purchases,record['purchase_id'])
            path=attachment_path(db.settings,record)
        return FileResponse(path,media_type=record['media_type'],filename=record['filename'],content_disposition_type='attachment',
                            headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    @routes.delete('/attachments/{identifier}')
    def attachment_delete(identifier: UUID, operation_id: UUID, actor_id: UUID, client_time: AwareDatetime,
                          expected_revision: int = Query(...,ge=1)):
        operation=AttachmentDeleteOperation(operation_id=operation_id,entity_id=identifier,actor_id=actor_id,
                                            client_time=client_time,data={'expected_revision':expected_revision})
        return service.execute(operation)

    @routes.get('/installations/{identifier}')
    def installation_detail(identifier: UUID):
        with db.transaction() as c:
            installation=get(c,s.installations,identifier)
            subscription=c.execute(select(s.subscriptions).where(s.subscriptions.c.installation_id==str(identifier))).mappings().first()
            return {'installation':installation,'subscription':{k:subscription[k] for k in ['id','revision','active']} if subscription else None}

    @routes.get('/household')
    def household():
        with db.transaction() as c:
            return service.household(c)

    @routes.get('/avatar-options')
    def avatars():
        return avatar_options()

    @routes.get('/records/{resource}/{identifier}')
    def record(resource: str, identifier: str):
        table = s.RESOURCES.get(resource)
        if table is None:
            raise DomainError('not_found', 'Unknown resource', 404)
        with db.transaction() as c:
            return service.request_detail(c, identifier) if resource=='approval-requests' else get(c, table, identifier)

    def collection(resource):
        def list_records(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                         month: str | None = None, category_id: str | None = None,
                         owner_id: str | None = None, recipient_id: str | None = None,
                         target_id: str | None = None, active: bool | None = None, status: str | None = None):
            table = s.RESOURCES[resource]
            query=select(table).where(table.c.deleted == False)
            filters={'category_id':category_id,'recipient_id':recipient_id,'target_id':target_id,'active':active,'status':status}
            if owner_id is not None:
                column=next((x for x in ['owner_id','purchaser_id','requester_id','user_id','actor_id'] if x in table.c),None)
                if column is None:
                    raise DomainError('filter','Owner filter is unavailable for this resource')
                query=query.where(table.c[column]==owner_id)
            for key,value in filters.items():
                if value is not None:
                    if key not in table.c:
                        raise DomainError('filter',f'{key} filter is unavailable for this resource')
                    query=query.where(table.c[key]==value)
            if month is not None:
                start,end=month_bounds(month)
                if 'transaction_date' not in table.c:
                    raise DomainError('filter','Month filter is unavailable for this resource')
                query=query.where(table.c.transaction_date.between(start,end))
            with db.transaction() as c:
                rows=[dict(x) for x in c.execute(query.order_by(table.c.id).limit(limit).offset(offset)).mappings()]
                if resource=='approval-requests':
                    rows=[service.request_detail(c,x['id']) for x in rows]
                return {'items': rows, 'limit': limit, 'offset': offset}
        return list_records

    @routes.get('/budget-months/{month}')
    def budget(month: str):
        with db.transaction() as c:
            return service.summary(c, month)

    @routes.get('/bill-occurrences')
    def bills(month: str):
        with db.transaction() as c:
            return {'items': service.upcoming_bills(c, month)}

    for resource in ('users', 'categories', 'notifications', 'purchases', 'income', 'savings', 'recurring-bills', 'wishlist-items', 'approval-requests', 'comments'):
        routes.add_api_route('/'+resource, collection(resource), methods=['GET'], name='list_'+resource)
    return routes
