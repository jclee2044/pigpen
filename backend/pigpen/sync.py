from sqlalchemy import select, func
from . import schema as s
from .errors import DomainError

OFFLINE_KINDS={'purchase.create','request.create','vote.set'}


def push(service, operations):
    outcomes=[]
    for operation in operations:
        try:
            if operation.kind not in OFFLINE_KINDS:
                raise DomainError('online_only','This operation requires the online endpoint')
            outcomes.append({'ok':True,**service.execute(operation)})
        except DomainError as exc:
            outcomes.append({'ok':False,'operation_id':str(operation.operation_id),'status':exc.status,**exc.body()})
    return {'outcomes':outcomes}


def pull(db,cursor,limit):
    with db.transaction() as c:
        head=c.execute(select(func.max(s.changes.c.cursor))).scalar() or 0
        if cursor>head:
            raise DomainError('cursor','Unknown sync cursor; fetch a snapshot',409)
        rows=list(c.execute(select(s.changes).where(s.changes.c.cursor>cursor).order_by(s.changes.c.cursor).limit(limit+1)).mappings())
        page=[dict(r) for r in rows[:limit]]
        return {'changes':page,'next_cursor':page[-1]['cursor'] if page else cursor,'has_more':len(rows)>limit}


def snapshot(db):
    with db.transaction() as c:
        # BEGIN establishes the same SQLite read snapshot for head and all tables.
        head=c.execute(select(func.max(s.changes.c.cursor))).scalar() or 0
        records={resource:[dict(r) for r in c.execute(select(table)).mappings()] for resource,table in s.RESOURCES.items()}
        return {'cursor':head,'records':records}
