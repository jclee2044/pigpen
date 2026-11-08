"""Persist each owner's wish-list order."""
from alembic import op
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN wishlist_order JSON NOT NULL DEFAULT '[]'")


def downgrade():
    raise RuntimeError('Restore a verified backup')
