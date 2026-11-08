"""Allow closed, denied approval requests while preserving history."""
from alembic import op
from sqlalchemy import MetaData, Table, CheckConstraint

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    table = Table('approval_requests', MetaData(), autoload_with=op.get_bind())
    for constraint in table.constraints:
        if isinstance(constraint, CheckConstraint) and 'status IN' in str(constraint.sqltext):
            constraint.name = 'request_status'
    with op.batch_alter_table('approval_requests', copy_from=table, recreate='always') as batch:
        batch.drop_constraint('request_status', type_='check')
        batch.create_check_constraint('request_status', "status IN ('open','canceled','purchased','denied')")


def downgrade():
    raise RuntimeError('Restore a verified backup')
