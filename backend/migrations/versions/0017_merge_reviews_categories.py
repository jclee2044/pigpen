"""Join independent monthly category and review migrations in the shared checkout."""
revision = '0017'
down_revision = ('0015', '0016')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    raise RuntimeError('Preserve post-upgrade records')
