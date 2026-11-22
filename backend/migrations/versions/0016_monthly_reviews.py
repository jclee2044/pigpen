"""Durable monthly analyses, independent of monthly-category changes."""
from alembic import op
import sqlalchemy as sa

revision = '0016'
down_revision = '0014'
branch_labels = ('monthly_reviews',)
depends_on = None


def upgrade():
    op.create_table('monthly_review_schedule',
        sa.Column('household_id', sa.String, sa.ForeignKey('households.id'), primary_key=True),
        sa.Column('first_month', sa.String, nullable=False))
    op.create_table('monthly_reviews',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('household_id', sa.String, sa.ForeignKey('households.id'), nullable=False),
        sa.Column('month', sa.String, nullable=False),
        sa.Column('status', sa.String, nullable=False),
        sa.Column('created_at', sa.String),
        sa.Column('snapshot', sa.JSON), sa.Column('report', sa.JSON),
        sa.Column('source_hash', sa.String),
        sa.Column('attempts', sa.Integer, nullable=False),
        sa.Column('next_attempt', sa.String, nullable=False),
        sa.Column('lease_until', sa.String), sa.Column('lease_token', sa.String),
        sa.UniqueConstraint('household_id', 'month'))


def downgrade():
    raise RuntimeError('Retain reports; restore only into a new data directory')
