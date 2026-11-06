"""Monthly allocations and purchases."""
from alembic import op
revision="0003"
down_revision="0002"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE TABLE budget_months (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tmonth VARCHAR NOT NULL, \n\texpected_income_minor INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (expected_income_minor >= 0), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tUNIQUE (month)\n)")
    op.execute("CREATE TABLE allocations (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tbudget_month_id VARCHAR NOT NULL, \n\tcategory_id VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (amount_minor >= 0), \n\tUNIQUE (budget_month_id, category_id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(budget_month_id) REFERENCES budget_months (id), \n\tFOREIGN KEY(category_id) REFERENCES categories (id)\n)")
    op.execute("CREATE TABLE purchases (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tpurchaser_id VARCHAR NOT NULL, \n\tcategory_id VARCHAR NOT NULL, \n\titem VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\ttransaction_date VARCHAR NOT NULL, \n\tmerchant VARCHAR, \n\tdescription VARCHAR NOT NULL, \n\trequest_id VARCHAR, \n\tbill_id VARCHAR, \n\tbill_due VARCHAR, \n\tPRIMARY KEY (id), \n\tCHECK (amount_minor > 0), \n\tUNIQUE (bill_id, bill_due), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(purchaser_id) REFERENCES users (id), \n\tFOREIGN KEY(category_id) REFERENCES categories (id), \n\tUNIQUE (request_id)\n)")
    op.execute('CREATE INDEX purchases_month_category ON purchases (transaction_date, category_id)')

def downgrade():
    raise RuntimeError("Restore a verified backup")
