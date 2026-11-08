"""Store allocation percentages alongside exact cent amounts."""
from alembic import op
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE allocations ADD COLUMN percentage_basis_points INTEGER')
    op.execute('''UPDATE allocations SET percentage_basis_points = (
        SELECT CASE WHEN expected_income_minor > 0
            THEN (allocations.amount_minor * 10000 + expected_income_minor / 2) / expected_income_minor
            ELSE NULL END FROM budget_months WHERE id = allocations.budget_month_id
    )''')


def downgrade():
    raise RuntimeError('Restore a verified backup')
