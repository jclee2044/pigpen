from typing import Literal
from fastapi import APIRouter, Query
from sqlalchemy import select
from .contracts import Operation
from .service import Service, get, avatar_options
from . import schema as s
from .errors import DomainError


def router(db):
    routes = APIRouter(prefix='/api/v1')
    service = Service(db)

    @routes.post('/operations')
    def execute(operation: Operation):
        return service.execute(operation)

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
            return get(c, table, identifier)

    def collection(resource):
        def list_records(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
            table = s.RESOURCES[resource]
            with db.transaction() as c:
                rows = c.execute(select(table).where(table.c.deleted == False).order_by(table.c.id).limit(limit).offset(offset)).mappings()
                return {'items': [dict(x) for x in rows], 'limit': limit, 'offset': offset}
        return list_records

    @routes.get('/budget-months/{month}')
    def budget(month: str):
        with db.transaction() as c:
            return service.summary(c, month)

    for resource in ('users', 'categories', 'notifications', 'purchases'):
        routes.add_api_route('/'+resource, collection(resource), methods=['GET'], name='list_'+resource)
    return routes
