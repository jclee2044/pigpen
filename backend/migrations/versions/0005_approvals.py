"""Wish lists, revisioned unanimous approvals and comments."""
from alembic import op
revision="0005"
down_revision="0004"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE TABLE comments (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tactor_id VARCHAR NOT NULL, \n\ttarget_resource VARCHAR NOT NULL, \n\ttarget_id VARCHAR NOT NULL, \n\ttext VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (target_resource IN ('wishlist-items','approval-requests')), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(actor_id) REFERENCES users (id)\n)")
    op.execute("CREATE TABLE wishlist_items (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\towner_id VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tprice_minor INTEGER NOT NULL, \n\tdescription VARCHAR NOT NULL, \n\turl VARCHAR, \n\tstatus VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (price_minor >= 0), \n\tCHECK (status IN ('active','purchased','archived')), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(owner_id) REFERENCES users (id)\n)")
    op.execute("CREATE TABLE approval_requests (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\trequester_id VARCHAR NOT NULL, \n\titem VARCHAR NOT NULL, \n\tamount_minor INTEGER NOT NULL, \n\tdescription VARCHAR NOT NULL, \n\turl VARCHAR, \n\tcategory_id VARCHAR, \n\tstatus VARCHAR NOT NULL, \n\tpurchase_id VARCHAR, \n\tapproved_revision INTEGER, \n\tPRIMARY KEY (id), \n\tCHECK (amount_minor > 0), \n\tCHECK (status IN ('open','canceled','purchased')), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(requester_id) REFERENCES users (id), \n\tFOREIGN KEY(category_id) REFERENCES categories (id), \n\tUNIQUE (purchase_id)\n)")
    op.execute("CREATE TABLE approval_votes (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\trequest_id VARCHAR NOT NULL, \n\treviewer_id VARCHAR NOT NULL, \n\tapproved BOOLEAN NOT NULL, \n\trequest_revision INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (request_id, reviewer_id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(request_id) REFERENCES approval_requests (id), \n\tFOREIGN KEY(reviewer_id) REFERENCES users (id)\n)")

def downgrade():
    raise RuntimeError("Restore a verified backup")
