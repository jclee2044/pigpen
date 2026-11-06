"""Income, savings and monthly bills."""
from alembic import op
revision="0004"
down_revision="0003"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE TABLE income_entries (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\tdescription VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\ttransaction_date VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (amount_minor > 0), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)")
    op.execute("CREATE TABLE savings_entries (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\ttransaction_date VARCHAR NOT NULL, \n\tdescription VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (kind IN ('opening','contribution','withdrawal')), \n\tCHECK (amount_minor >= 0), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)")
    op.execute("CREATE UNIQUE INDEX one_savings_opening ON savings_entries (household_id) WHERE kind = 'opening' AND deleted = 0")
    op.execute("CREATE TABLE recurring_bills (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\tcategory_id VARCHAR NOT NULL, \n\tdue_day INTEGER NOT NULL, \n\tstart_date VARCHAR NOT NULL, \n\tdescription VARCHAR NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (amount_minor > 0), \n\tCHECK (due_day BETWEEN 1 AND 31), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(category_id) REFERENCES categories (id)\n)")
    op.execute("CREATE TABLE bill_occurrences (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tbill_id VARCHAR NOT NULL, \n\tdue_date VARCHAR NOT NULL, \n\texpected_minor INTEGER NOT NULL, \n\tpurchase_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (bill_id, due_date), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(bill_id) REFERENCES recurring_bills (id), \n\tUNIQUE (purchase_id), \n\tFOREIGN KEY(purchase_id) REFERENCES purchases (id)\n)")

def downgrade():
    raise RuntimeError("Restore a verified backup")
