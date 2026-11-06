"""Consistent database snapshots plus immutable attachment objects. No overwrites."""
from datetime import datetime, timezone
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
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Database integrity validation failed')


def _publish(stage,destination):
    if destination.exists():
        raise FileExistsError('Refusing to replace an existing destination')
    stage.rename(destination)


def backup(settings,destination):
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
        with sqlite3.connect(settings.database_path.as_uri()+'?mode=ro',uri=True) as source:
            with sqlite3.connect(output) as target:
                source.backup(target)
        check_database(output)
        files={'pigpen.sqlite3':digest(output)}
        # Read references from the snapshot, never from the now-moving live database.
        with sqlite3.connect(output) as snapshot:
            attachments=snapshot.execute('SELECT storage_key,checksum FROM attachments').fetchall()
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


def restore(source,destination,environment):
    source=Path(source).resolve()
    settings=Settings(Path(destination),environment)
    destination=settings.data_dir
    if destination.exists():
        raise FileExistsError('Restore requires a new directory; existing financial data is never replaced')
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
    with sqlite3.connect((source/'pigpen.sqlite3').as_uri()+'?mode=ro',uri=True) as c:
        for key,expected in c.execute('SELECT storage_key,checksum FROM attachments'):
            if files.get('uploads/'+key)!=expected:
                raise ValueError('Backup is missing a referenced attachment')
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
