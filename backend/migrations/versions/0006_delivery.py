"""Immutable attachment metadata and installation-bound push delivery."""
from alembic import op
revision="0006"
down_revision="0005"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE TABLE installations (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)")
    op.execute("CREATE TABLE subscriptions (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tinstallation_id VARCHAR NOT NULL, \n\tendpoint VARCHAR NOT NULL, \n\tp256dh VARCHAR NOT NULL, \n\tauth VARCHAR NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tUNIQUE (installation_id), \n\tFOREIGN KEY(installation_id) REFERENCES installations (id), \n\tUNIQUE (endpoint)\n)")
    op.execute("CREATE TABLE attachments (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tpurchase_id VARCHAR NOT NULL, \n\tuploader_id VARCHAR NOT NULL, \n\tstorage_key VARCHAR NOT NULL, \n\tfilename VARCHAR NOT NULL, \n\tmedia_type VARCHAR NOT NULL, \n\tbyte_size INTEGER NOT NULL, \n\tchecksum VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(household_id) REFERENCES households (id), \n\tFOREIGN KEY(purchase_id) REFERENCES purchases (id), \n\tFOREIGN KEY(uploader_id) REFERENCES users (id)\n)")
    op.execute('CREATE TABLE push_deliveries (\n\tid VARCHAR NOT NULL, \n\tnotification_id VARCHAR NOT NULL, \n\tsubscription_id VARCHAR NOT NULL, \n\tbinding_revision INTEGER NOT NULL, \n\tdelivered_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (notification_id, subscription_id, binding_revision), \n\tFOREIGN KEY(notification_id) REFERENCES notifications (id), \n\tFOREIGN KEY(subscription_id) REFERENCES subscriptions (id)\n)')

def downgrade():
    raise RuntimeError("Restore a verified backup")
