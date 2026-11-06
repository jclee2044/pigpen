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

budget_months = Table('budget_months', metadata, *record_columns(),
    Column('month', String, nullable=False, unique=True), Column('expected_income_minor', Integer, nullable=False),
    CheckConstraint('expected_income_minor >= 0'))
allocations = Table('allocations', metadata, *record_columns(),
    Column('budget_month_id', String, ForeignKey('budget_months.id'), nullable=False),
    Column('category_id', String, ForeignKey('categories.id'), nullable=False),
    Column('amount_minor', Integer, nullable=False), CheckConstraint('amount_minor >= 0'),
    UniqueConstraint('budget_month_id', 'category_id'))
purchases = Table('purchases', metadata, *record_columns(),
    Column('purchaser_id', String, ForeignKey('users.id'), nullable=False),
    Column('category_id', String, ForeignKey('categories.id'), nullable=False),
    Column('item', String, nullable=False), Column('amount_minor', Integer, nullable=False),
    Column('transaction_date', String, nullable=False), Column('merchant', String), Column('description', String, nullable=False),
    Column('request_id', String, unique=True), Column('bill_id', String), Column('bill_due', String),
    CheckConstraint('amount_minor > 0'), UniqueConstraint('bill_id', 'bill_due'))
Index('purchases_month_category', purchases.c.transaction_date, purchases.c.category_id)
RESOURCES.update({'budget-months': budget_months, 'allocations': allocations, 'purchases': purchases})

income_entries = Table('income_entries', metadata, *record_columns(),
    Column('user_id', String, ForeignKey('users.id'), nullable=False), Column('description', String, nullable=False),
    Column('amount_minor', Integer, nullable=False), Column('transaction_date', String, nullable=False),
    CheckConstraint('amount_minor > 0'))
savings_entries = Table('savings_entries', metadata, *record_columns(),
    Column('user_id', String, ForeignKey('users.id'), nullable=False), Column('kind', String, nullable=False),
    Column('amount_minor', Integer, nullable=False), Column('transaction_date', String, nullable=False), Column('description', String, nullable=False),
    CheckConstraint("kind IN ('opening','contribution','withdrawal')"), CheckConstraint('amount_minor >= 0'))
Index('one_savings_opening', savings_entries.c.household_id, unique=True,
      sqlite_where=(savings_entries.c.kind=='opening') & (savings_entries.c.deleted==False))
recurring_bills = Table('recurring_bills', metadata, *record_columns(),
    Column('name', String, nullable=False), Column('amount_minor', Integer, nullable=False),
    Column('category_id', String, ForeignKey('categories.id'), nullable=False),
    Column('due_day', Integer, nullable=False), Column('start_date', String, nullable=False),
    Column('description', String, nullable=False), Column('active', Boolean, nullable=False),
    CheckConstraint('amount_minor > 0'), CheckConstraint('due_day BETWEEN 1 AND 31'))
bill_occurrences = Table('bill_occurrences', metadata, *record_columns(),
    Column('bill_id', String, ForeignKey('recurring_bills.id'), nullable=False), Column('due_date', String, nullable=False),
    Column('expected_minor', Integer, nullable=False), Column('purchase_id', String, ForeignKey('purchases.id'), nullable=False, unique=True),
    UniqueConstraint('bill_id','due_date'))
RESOURCES.update({'income':income_entries,'savings':savings_entries,'recurring-bills':recurring_bills,'bill-occurrences':bill_occurrences})
