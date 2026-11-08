"""Shared category hierarchies and the Subscriptions parent."""
from uuid import uuid5, NAMESPACE_URL
from alembic import op
from sqlalchemy import select
from pigpen import schema as s
from pigpen.service import Service

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    # Rebuild the original table with relaxed expense-parent constraints. The
    # migration runner disables FK enforcement before BEGIN and validates before
    # COMMIT, preserving references from purchases, bills, allocations and self.
    original = connection.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='categories'").scalar_one()
    old_check = "(kind = 'personal' AND owner_id IS NOT NULL) OR (kind != 'personal' AND owner_id IS NULL AND parent_id IS NULL)"
    new_check = "(kind = 'personal' AND owner_id IS NOT NULL) OR (kind = 'expense' AND owner_id IS NULL) OR (kind = 'savings' AND owner_id IS NULL AND parent_id IS NULL)"
    assert old_check in original
    replacement = original.replace('CREATE TABLE categories', 'CREATE TABLE categories_new', 1).replace(old_check, new_check)
    connection.exec_driver_sql(replacement)
    connection.exec_driver_sql('INSERT INTO categories_new SELECT * FROM categories')
    connection.exec_driver_sql('DROP TABLE categories')
    connection.exec_driver_sql('ALTER TABLE categories_new RENAME TO categories')
    connection.exec_driver_sql("CREATE UNIQUE INDEX one_personal_parent ON categories (owner_id) WHERE kind = 'personal' AND parent_id IS NULL")
    connection.exec_driver_sql('ALTER TABLE categories ADD COLUMN allows_subcategories BOOLEAN NOT NULL DEFAULT 0 CHECK (parent_id IS NULL OR allows_subcategories = 0)')
    # Historical migrations must read the schema at this revision.
    class MigrationService(Service):
        def household(self, c):
            return dict(c.exec_driver_sql('SELECT * FROM households').mappings().first())
    service = MigrationService(None)
    for row in connection.execute(select(s.categories).where(s.categories.c.kind == 'personal', s.categories.c.parent_id.is_(None))).mappings().all():
        service.save(connection, s.categories, {'allows_subcategories': True}, dict(row))
    household = connection.exec_driver_sql('SELECT * FROM households').mappings().first()
    if household:
        existing = connection.execute(select(s.categories).where(
            s.categories.c.parent_id.is_(None), s.categories.c.kind == 'expense',
            s.categories.c.deleted.is_(False))).mappings().all()
        subscriptions = next((dict(row) for row in existing if row['name'].strip().casefold() == 'subscriptions'), None)
        if subscriptions:
            service.save(connection, s.categories, {'allows_subcategories': True}, subscriptions)
        else:
            service.save(connection, s.categories, dict(
                id=str(uuid5(NAMESPACE_URL, household['id'] + '/Subscriptions')),
                name='Subscriptions', kind='expense', owner_id=None, parent_id=None,
                active=True, allows_subcategories=True))


def downgrade():
    raise RuntimeError('Restore a verified backup')
