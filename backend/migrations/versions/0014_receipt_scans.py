"""Durable receipt suggestions and image retention; additive only."""
from alembic import op
import sqlalchemy as sa
revision='0014'
down_revision='0013'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('receipt_scans',
        sa.Column('id',sa.String,primary_key=True),sa.Column('household_id',sa.String,sa.ForeignKey('households.id'),nullable=False),
        sa.Column('revision',sa.Integer,nullable=False),sa.Column('deleted',sa.Boolean,nullable=False),
        sa.Column('created_at',sa.String,nullable=False),sa.Column('updated_at',sa.String,nullable=False),
        sa.Column('actor_id',sa.String,sa.ForeignKey('users.id'),nullable=False),
        sa.Column('payload_hash',sa.String,nullable=False),sa.Column('status',sa.String,nullable=False),
        sa.Column('storage_key',sa.String,nullable=False),sa.Column('checksum',sa.String,nullable=False),
        sa.Column('filename',sa.String,nullable=False),sa.Column('media_type',sa.String,nullable=False),
        sa.Column('byte_size',sa.Integer,nullable=False),sa.Column('suggestions',sa.JSON),
        sa.Column('error',sa.String),sa.Column('attempts',sa.Integer,nullable=False),
        sa.Column('lease_until',sa.String),sa.Column('lease_token',sa.String),
        sa.Column('expires_at',sa.String,nullable=False),sa.Column('keep_indefinitely',sa.Boolean,nullable=False),
        sa.Column('expired_at',sa.String),sa.Column('purchase_id',sa.String,sa.ForeignKey('purchases.id'),unique=True))
    op.create_index('receipt_queue','receipt_scans',['status','created_at'])
    for name,kind in [('receipt_scan_id',sa.String),('expires_at',sa.String),('expired_at',sa.String)]:
        op.add_column('attachments',sa.Column(name,kind))
    op.add_column('attachments',sa.Column('keep_indefinitely',sa.Boolean,nullable=False,server_default='0'))

def downgrade():
    raise RuntimeError('Restore a verified backup')
