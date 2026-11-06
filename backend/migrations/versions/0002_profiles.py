"""Profiles and category relationships."""
from alembic import op
revision="0002"
down_revision="0001"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE TABLE users (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tname_key VARCHAR NOT NULL, \n\tavatar JSON NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tUNIQUE (name_key)\n)")
    op.execute("CREATE TABLE categories (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\towner_id VARCHAR, \n\tparent_id VARCHAR, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (kind IN ('expense','personal','savings')), \n\tCHECK ((kind = 'personal' AND owner_id IS NOT NULL) OR (kind != 'personal' AND owner_id IS NULL AND parent_id IS NULL)), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(owner_id) REFERENCES users (id), \n\tFOREIGN KEY(parent_id) REFERENCES categories (id)\n)")
    op.execute("CREATE UNIQUE INDEX one_personal_parent ON categories (owner_id) WHERE kind = 'personal' AND parent_id IS NULL")

def downgrade():
    raise RuntimeError("Restore a verified backup")
