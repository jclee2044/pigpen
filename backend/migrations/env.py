from alembic import context
from pigpen.schema import metadata

connection = context.config.attributes.get('connection')
if connection is None:
    raise RuntimeError('Run migrations through python -m pigpen migrate with explicit storage configuration')
context.configure(connection=connection, target_metadata=metadata, transactional_ddl=True, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
