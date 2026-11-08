"""Preserve existing display order as a household-wide wish order."""
import json
from datetime import datetime,timezone
from alembic import op
from sqlalchemy import text
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE households ADD COLUMN wishlist_order JSON NOT NULL DEFAULT '[]'")
    c=op.get_bind()
    owners={row['id']:json.loads(row['wishlist_order']) for row in c.execute(text('SELECT id,wishlist_order FROM users')).mappings()}
    def rank(row):
        order=owners.get(row['owner_id'],[])
        return (row['owner_id'],order.index(row['id']) if row['id'] in order else float('inf'),row['created_at'],row['id'])
    wishes=c.execute(text('SELECT id,owner_id,created_at FROM wishlist_items WHERE deleted=0')).mappings().all()
    order=[row['id'] for row in sorted(wishes,key=rank)]
    stamp=datetime.now(timezone.utc).isoformat()
    c.execute(text('UPDATE households SET wishlist_order=:value,revision=revision+1,updated_at=:stamp'),{'value':json.dumps(order),'stamp':stamp})
    for row in c.execute(text('SELECT * FROM households')).mappings():
        record=dict(row)
        for field in ['category_order','wishlist_order']:
            record[field]=json.loads(record[field])
        record['deleted']=bool(record['deleted'])
        c.execute(text("INSERT INTO changes (resource,record) VALUES ('household',:record)"),{'record':json.dumps(record)})


def downgrade():
    raise RuntimeError('Restore a verified backup')
