"""Explicit relational schema; JSON is limited to avatars, events and outcomes."""
from sqlalchemy import (MetaData, Table, Column, String, Integer, Boolean, JSON,
                        ForeignKey, CheckConstraint, UniqueConstraint, Index)

metadata = MetaData()


def record_columns():
    return [Column('id', String, primary_key=True),
            Column('household_id', String, ForeignKey('households.id'), nullable=False),
            Column('revision', Integer, nullable=False),
            Column('deleted', Boolean, nullable=False, server_default='0'),
            Column('created_at', String, nullable=False), Column('updated_at', String, nullable=False)]


households = Table('households', metadata,
    Column('id', String, primary_key=True), Column('singleton', Integer, nullable=False, unique=True),
    Column('name', String, nullable=False), Column('currency', String, nullable=False),
    Column('timezone', String, nullable=False), Column('approval_policy', String, nullable=False),
    Column('revision', Integer, nullable=False), Column('deleted', Boolean, nullable=False),
    Column('created_at', String, nullable=False), Column('updated_at', String, nullable=False),
    CheckConstraint('singleton = 1'), CheckConstraint("approval_policy = 'all'"))
operations = Table('operations', metadata,
    Column('id', String, primary_key=True), Column('payload_hash', String, nullable=False),
    Column('outcome', JSON, nullable=False), Column('created_at', String, nullable=False))
audit_events = Table('audit_events', metadata,
    Column('id', Integer, primary_key=True), Column('operation_id', String, nullable=False, unique=True),
    Column('actor_id', String), Column('kind', String, nullable=False), Column('target_id', String, nullable=False),
    Column('client_time', String, nullable=False), Column('server_time', String, nullable=False))
changes = Table('changes', metadata,
    Column('cursor', Integer, primary_key=True, autoincrement=True),
    Column('resource', String, nullable=False), Column('record', JSON, nullable=False),
    sqlite_autoincrement=True)
notifications = Table('notifications', metadata, *record_columns(),
    Column('recipient_id', String, nullable=False), Column('event_key', String, nullable=False),
    Column('kind', String, nullable=False), Column('target_resource', String, nullable=False),
    Column('target_id', String, nullable=False), Column('read_at', String),
    UniqueConstraint('recipient_id', 'event_key'))
outbox = Table('outbox', metadata,
    Column('id', String, primary_key=True), Column('notification_id', String, ForeignKey('notifications.id'), nullable=False, unique=True),
    Column('recipient_id', String, nullable=False), Column('attempts', Integer, nullable=False),
    Column('next_attempt', String, nullable=False), Column('delivered_at', String),
    Column('lease_until', String), Column('lease_token', String), Column('last_error', String))

RESOURCES = {'household': households, 'notifications': notifications}

users = Table('users', metadata, *record_columns(),
    Column('name', String, nullable=False), Column('name_key', String, nullable=False, unique=True),
    Column('avatar', JSON, nullable=False), Column('active', Boolean, nullable=False))
categories = Table('categories', metadata, *record_columns(),
    Column('name', String, nullable=False), Column('kind', String, nullable=False),
    Column('owner_id', String, ForeignKey('users.id')), Column('parent_id', String, ForeignKey('categories.id')),
    Column('active', Boolean, nullable=False),
    CheckConstraint("kind IN ('expense','personal','savings')"),
    CheckConstraint("(kind = 'personal' AND owner_id IS NOT NULL) OR (kind != 'personal' AND owner_id IS NULL AND parent_id IS NULL)"))
Index('one_personal_parent', categories.c.owner_id, unique=True,
      sqlite_where=(categories.c.kind == 'personal') & categories.c.parent_id.is_(None))
RESOURCES.update({'users': users, 'categories': categories})
