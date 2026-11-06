"""Storage, audit and durable event foundation."""
from alembic import op
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('CREATE TABLE audit_events (\n\tid INTEGER NOT NULL, \n\toperation_id VARCHAR NOT NULL, \n\tactor_id VARCHAR, \n\tkind VARCHAR NOT NULL, \n\ttarget_id VARCHAR NOT NULL, \n\tclient_time VARCHAR NOT NULL, \n\tserver_time VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (operation_id)\n)')
    op.execute('CREATE TABLE changes (\n\tcursor INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, \n\tresource VARCHAR NOT NULL, \n\trecord JSON NOT NULL\n)')
    op.execute("CREATE TABLE households (\n\tid VARCHAR NOT NULL, \n\tsingleton INTEGER NOT NULL, \n\tname VARCHAR NOT NULL, \n\tcurrency VARCHAR NOT NULL, \n\ttimezone VARCHAR NOT NULL, \n\tapproval_policy VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (singleton = 1), \n\tCHECK (approval_policy = 'all'), \n\tUNIQUE (singleton)\n)")
    op.execute('CREATE TABLE operations (\n\tid VARCHAR NOT NULL, \n\tpayload_hash VARCHAR NOT NULL, \n\toutcome JSON NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id)\n)')
    op.execute("CREATE TABLE notifications (\n\tid VARCHAR NOT NULL, \n\thousehold_id VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tdeleted BOOLEAN DEFAULT '0' NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\trecipient_id VARCHAR NOT NULL, \n\tevent_key VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\ttarget_resource VARCHAR NOT NULL, \n\ttarget_id VARCHAR NOT NULL, \n\tread_at VARCHAR, \n\tPRIMARY KEY (id), \n\tUNIQUE (recipient_id, event_key), \n\tFOREIGN KEY(household_id) REFERENCES households (id)\n)")
    op.execute('CREATE TABLE outbox (\n\tid VARCHAR NOT NULL, \n\tnotification_id VARCHAR NOT NULL, \n\trecipient_id VARCHAR NOT NULL, \n\tattempts INTEGER NOT NULL, \n\tnext_attempt VARCHAR NOT NULL, \n\tdelivered_at VARCHAR, \n\tlease_until VARCHAR, \n\tlease_token VARCHAR, \n\tlast_error VARCHAR, \n\tPRIMARY KEY (id), \n\tUNIQUE (notification_id), \n\tFOREIGN KEY(notification_id) REFERENCES notifications (id)\n)')

def downgrade():
    raise RuntimeError("Restore a verified backup; no automatic destructive downgrade")
