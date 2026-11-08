"""Persist the shared household category order."""
from alembic import op
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE households ADD COLUMN category_order JSON NOT NULL DEFAULT '[]'")


def downgrade():
    raise RuntimeError('Restore a verified backup')
