from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from .errors import DomainError

MIGRATIONS = Path(__file__).resolve().parents[1] / 'migrations'


def migration_config():
    config = Config()
    config.set_main_option('script_location', str(MIGRATIONS))
    return config


class Database:
    def __init__(self, settings):
        self.settings = settings
        self.engine = create_engine(URL.create('sqlite', database=str(settings.database_path)),
                                    poolclass=NullPool, connect_args={'check_same_thread': False, 'timeout': 5})

        @event.listens_for(self.engine, 'connect')
        def configure(dbapi, _):
            dbapi.isolation_level = None
            dbapi.execute('PRAGMA foreign_keys=ON')
            dbapi.execute('PRAGMA busy_timeout=5000')

        @event.listens_for(self.engine, 'begin')
        def begin(conn):
            conn.exec_driver_sql('BEGIN IMMEDIATE' if conn.get_execution_options().get('write') else 'BEGIN')

    @contextmanager
    def transaction(self, write=False):
        if not self.settings.database_path.is_file():
            raise DomainError('not_ready', 'Initialize storage with the migration command', 503)
        try:
            self.settings.verify_storage()
        except ValueError:
            raise DomainError('storage_environment', 'Data directory does not belong to this environment', 503) from None
        with self.engine.connect().execution_options(write=write) as conn:
            with conn.begin():
                yield conn

    def ready(self):
        if not self.settings.database_path.is_file():
            return False
        try:
            with self.transaction() as conn:
                current = conn.execute(text('SELECT version_num FROM alembic_version')).scalar()
                return current == ScriptDirectory.from_config(migration_config()).get_current_head()
        except Exception:
            return False


def migrate(settings, target='head'):
    settings.verify_storage(allow_new=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with settings.environment_marker.open('x') as marker:
            marker.write(settings.environment+'\n')
    except FileExistsError:
        settings.verify_storage()
    db = Database(settings)
    # Journal selection is outside a transaction; migrations themselves are atomic.
    import sqlite3
    with sqlite3.connect(settings.database_path) as raw:
        raw.execute('PRAGMA journal_mode=WAL')
    with db.engine.connect().execution_options(write=True) as conn:
        raw = conn.connection.driver_connection
        raw.execute('PRAGMA foreign_keys=OFF')
        try:
            with conn.begin():
                config = migration_config()
                config.attributes['connection'] = conn
                command.upgrade(config, target)
                if conn.exec_driver_sql('PRAGMA foreign_key_check').first():
                    raise ValueError('Migration failed foreign key validation')
        finally:
            raw.execute('PRAGMA foreign_keys=ON')
    db.engine.dispose()
