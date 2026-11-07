from datetime import date,timedelta
import pytest
from pigpen.recovery import scheduled_backup,restore
from pigpen.config import Settings
from pigpen.database import Database,migrate


def test_scheduled_snapshots_retention_and_restore(settings,client,users,tmp_path):
    root=tmp_path/'backups'
    for weeks in range(6):
        scheduled_backup(settings,root,date(2026,9,1)+timedelta(weeks=weeks))
    for days in range(10):
        scheduled_backup(settings,root,date(2026,10,13)+timedelta(days=days))
    assert len(list(root.glob('daily-*')))==7
    assert len(list(root.glob('weekly-*')))==4
    latest=root/'daily-2026-10-22'
    restored=restore(latest,tmp_path/'restored','development')
    assert Database(restored).ready()
    assert (latest/'manifest.json').is_file()
    other=Settings(tmp_path/'another','development');migrate(other)
    with pytest.raises(ValueError,match='another environment'):
        scheduled_backup(other,root)


def test_schedule_never_prunes_before_verification_or_deletes_unknown_files(settings,client,tmp_path):
    root=tmp_path/'backups'
    for day in range(7):
        scheduled_backup(settings,root,date(2026,10,1)+timedelta(days=day))
    oldest=root/'daily-2026-10-01'
    (oldest/'keep.txt').write_text('Unrelated file must survive')
    with pytest.raises(ValueError,match='Unrecognized files'):
        scheduled_backup(settings,root,date(2026,10,8))
    assert (oldest/'keep.txt').exists()
    assert (root/'daily-2026-10-08'/'manifest.json').exists()
    (root/'daily-2026-10-09').mkdir()
    with pytest.raises(FileNotFoundError):
        scheduled_backup(settings,root,date(2026,10,9))
    assert oldest.exists()
