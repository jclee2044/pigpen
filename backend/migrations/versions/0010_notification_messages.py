"""Persist approved notification previews without financial numbers."""
from alembic import op

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE notifications ADD COLUMN message VARCHAR NOT NULL DEFAULT ''")


def downgrade():
    raise RuntimeError('Restore a verified backup')
