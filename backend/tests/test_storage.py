from sqlalchemy import text
import pytest
from pigpen.config import Settings
from pigpen.database import Database, migrate


def test_migrations_pragmas_and_rollback(tmp_path):
    settings = Settings(tmp_path / 'data', 'test')
    db = Database(settings)
    assert not db.ready()
    migrate(settings)
    assert db.ready()
    migrate(settings)
    with db.transaction() as c:
        assert c.exec_driver_sql('PRAGMA foreign_keys').scalar() == 1
        assert c.exec_driver_sql('PRAGMA journal_mode').scalar() == 'wal'
        assert c.exec_driver_sql('PRAGMA busy_timeout').scalar() == 5000
    with pytest.raises(RuntimeError):
        with db.transaction(write=True) as c:
            c.execute(text("INSERT INTO operations VALUES ('x','h','{}','now')"))
            raise RuntimeError('simulated failure')
    with db.transaction() as c:
        assert c.execute(text('SELECT COUNT(*) FROM operations')).scalar() == 0
