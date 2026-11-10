"""Consistent database snapshots plus immutable attachment objects. No overwrites."""
from datetime import datetime, timezone
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3
from uuid import uuid4
from .config import Settings, PROJECT_ROOT


def digest(path):
    h=sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def external_path(path):
    path=Path(path)
    if not path.is_absolute():
        raise ValueError('Use an absolute destination outside the checkout')
    path=path.resolve()
    if path==PROJECT_ROOT or path.is_relative_to(PROJECT_ROOT):
        raise ValueError('Backups and runtime data must stay outside the Git checkout')
    return path


def check_database(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Database integrity validation failed')


def _publish(stage,destination):
    if destination.exists():
        raise FileExistsError('Refusing to replace an existing destination')
    stage.rename(destination)


def image_references(connection):
    columns={r[1] for r in connection.execute('PRAGMA table_info(attachments)')}
    if 'expired_at' not in columns:
        return connection.execute('SELECT storage_key,checksum FROM attachments').fetchall()
    # Preserve non-expired metadata references even when overdue until cleanup runs.
    return connection.execute('SELECT storage_key,checksum FROM attachments WHERE expired_at IS NULL UNION SELECT storage_key,checksum FROM receipt_scans WHERE expired_at IS NULL').fetchall()


def backup(settings,destination):
    from .image_lock import image_lock
    # Older schema backups must remain possible before upgrading.
    with closing(sqlite3.connect(settings.database_path.as_uri()+'?mode=ro',uri=True)) as c:
        has_scans=c.execute("SELECT 1 FROM sqlite_master WHERE name='receipt_scans'").fetchone()
    if has_scans:
        from .receipt_worker import cleanup
        from .database import Database
        cleanup(Database(settings))
    with image_lock(settings):
        return _backup(settings,destination)


def _backup(settings,destination):
    settings.verify_storage()
    destination=external_path(destination)
    if destination.exists() or destination.is_relative_to(settings.data_dir) or settings.data_dir.is_relative_to(destination):
        raise ValueError('Choose a new backup directory separate from runtime data')
    if not settings.database_path.is_file():
        raise ValueError('Source database does not exist')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=destination.with_name('.'+destination.name+'.incomplete-'+str(uuid4()))
    stage.mkdir(mode=0o700)
    try:
        output=stage/'pigpen.sqlite3'
        # The live source MUST see committed WAL pages; immutable applies only to frozen snapshots.
        with closing(sqlite3.connect(settings.database_path.as_uri()+'?mode=ro',uri=True)) as source:
            with closing(sqlite3.connect(output)) as target:
                source.backup(target)
        check_database(output)
        files={'pigpen.sqlite3':digest(output)}
        # Read references from the snapshot, never from the now-moving live database.
        with closing(sqlite3.connect(output.as_uri()+'?mode=ro&immutable=1',uri=True)) as snapshot:
            attachments=image_references(snapshot)
        for key,expected in attachments:
            if not re.fullmatch(r'[0-9a-f]{64}\.(png|jpg|webp)',key):
                raise ValueError('Invalid attachment reference')
            original=settings.uploads_dir/key
            if original.is_symlink() or not original.is_file() or digest(original)!=expected:
                raise ValueError('Referenced attachment is missing or corrupt')
            (stage/'uploads').mkdir(exist_ok=True,mode=0o700)
            if not (stage/'uploads'/key).exists():
                shutil.copyfile(original,stage/'uploads'/key)
            files['uploads/'+key]=expected
        (stage/'manifest.json').write_text(json.dumps({'format':1,'created_at':datetime.now(timezone.utc).isoformat(),'files':files},indent=2)+'\n')
        _publish(stage,destination)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise
    return destination


def validate_backup(source):
    source=Path(source).resolve()
    manifest=json.loads((source/'manifest.json').read_text())
    files=manifest.get('files',{})
    if manifest.get('format')!=1 or 'pigpen.sqlite3' not in files:
        raise ValueError('Unsupported backup manifest')
    # Exact allowed paths: no arbitrary copy destinations, symlinks or traversal.
    for name,expected in files.items():
        if name!='pigpen.sqlite3' and not re.fullmatch(r'uploads/[0-9a-f]{64}\.(png|jpg|webp)',name):
            raise ValueError('Unsafe backup path')
        path=source/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(source) or digest(path)!=expected:
            raise ValueError('Backup checksum validation failed')
    check_database(source/'pigpen.sqlite3')
    with closing(sqlite3.connect((source/'pigpen.sqlite3').as_uri()+'?mode=ro&immutable=1',uri=True)) as c:
        for key,expected in image_references(c):
            if files.get('uploads/'+key)!=expected:
                raise ValueError('Backup is missing a referenced attachment')
    return files


def restore(source,destination,environment):
    source=Path(source).resolve()
    settings=Settings(Path(destination),environment)
    destination=settings.data_dir
    if destination.exists():
        raise FileExistsError('Restore requires a new directory; existing financial data is never replaced')
    files=validate_backup(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=destination.with_name('.'+destination.name+'.restore-'+str(uuid4()));stage.mkdir(mode=0o700)
    try:
        for name in files:
            target=stage/name;target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source/name,target)
            if digest(target)!=files[name]:
                raise ValueError('Restored file checksum validation failed')
        check_database(stage/'pigpen.sqlite3')
        (stage/'.pigpen-environment').write_text(environment+'\n')
        _publish(stage,destination)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise
    return settings


def scheduled_backup(settings, destination, day=None):
    """Keep seven daily and four weekly full snapshots in a dedicated managed root."""
    import fcntl
    from zoneinfo import ZoneInfo
    settings.verify_storage()
    raw=Path(destination)
    if raw.is_symlink():
        raise ValueError('Backup root must not be a symbolic link')
    root=external_path(raw)
    if root.is_relative_to(settings.data_dir) or settings.data_dir.is_relative_to(root):
        raise ValueError('Backup root must be separate from runtime data')
    expected={'format':1,'source':str(settings.data_dir),'environment':settings.environment}
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    marker=root/'.pigpen-backups.json'
    if marker.is_symlink():
        raise ValueError('Invalid backup registration')
    if not marker.exists():
        if any(root.iterdir()):
            raise ValueError('Scheduled backups require a new dedicated destination')
        with marker.open('x') as output:
            json.dump(expected,output)
    if json.loads(marker.read_text())!=expected:
        raise ValueError('Backup root belongs to another environment or source')
    lock=root/'.backup.lock'
    if lock.is_symlink():
        raise ValueError('Invalid backup lock')
    with lock.open('a') as held:
        fcntl.flock(held,fcntl.LOCK_EX)
        day=day or datetime.now(ZoneInfo('America/New_York')).date()
        names=['daily-'+day.isoformat(),'weekly-'+day.strftime('%G-W%V')]
        # Publish and verify both current recovery points before considering retention.
        for name in names:
            target=root/name
            if target.is_symlink():
                raise ValueError('Backup snapshots must not be symbolic links')
            if not target.exists():
                backup(settings,target)
            validate_backup(target)
        expired=[]
        for pattern,count in [(r'daily-\d{4}-\d{2}-\d{2}',7),(r'weekly-\d{4}-W\d{2}',4)]:
            snapshots=sorted([p for p in root.iterdir() if re.fullmatch(pattern,p.name)],key=lambda p:p.name,reverse=True)
            for path in snapshots:
                if path.is_symlink() or not path.is_dir():
                    raise ValueError('Invalid managed backup snapshot')
            expired.extend(snapshots[count:])
        for path in expired:
            files=validate_backup(path)
            # Do not delete unrelated files even if placed inside an old snapshot.
            actual={str(p.relative_to(path)) for p in path.rglob('*') if p.is_file() or p.is_symlink()}
            if actual!=set(files)|{'manifest.json'} or any(p.is_symlink() for p in path.rglob('*')):
                raise ValueError('Unrecognized files in a retained snapshot; manual review required')
        for path in expired:
            shutil.rmtree(path)
    return root
