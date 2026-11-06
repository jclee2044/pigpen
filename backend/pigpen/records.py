from datetime import datetime, timezone
from pathlib import Path
import json
from sqlalchemy import select
from .errors import DomainError


def now():
    return datetime.now(timezone.utc).isoformat()


def avatar_options():
    path = Path(__file__).resolve().parents[2] / 'assets/avatars/pig-v1/manifest.json'
    return json.loads(path.read_text())


def get(conn, table, identifier, active=False):
    row = conn.execute(select(table).where(table.c.id == str(identifier))).mappings().first()
    if not row or row.get('deleted', False):
        raise DomainError('not_found', 'Record not found', 404)
    row = dict(row)
    if active and not row.get('active', True):
        raise DomainError('archived', 'Record is archived', 409)
    return row


def expect(row, revision):
    if row['revision'] != revision:
        raise DomainError('revision_conflict', 'Record changed; review its current revision', 409, row)
