import json
from pathlib import Path
import subprocess
import sys
import os
import pytest
from fastapi.testclient import TestClient
from conftest import submit
from test_attachments_push import purchase, png
from uuid import uuid4
from pigpen.recovery import backup, restore
from pigpen.database import Database, migrate
from pigpen.app import create_app


def test_backup_restore_financials_attachments_and_replay(client,users,settings,tmp_path):
    actor=users[0]['id'];p=purchase(client,actor)
    first=client.post(f"/api/v1/purchases/{p['id']}/attachments",data=dict(operation_id=str(uuid4()),actor_id=actor,
        client_time='2026-11-06T12:00:00Z'),files={'file':('receipt.png',png(),'image/png')})
    assert first.status_code==200
    destination=tmp_path/'snapshot'
    backup(settings,destination)
    recovered=restore(destination,tmp_path/'restored','test')
    assert Database(recovered).ready()
    with TestClient(create_app(recovered)) as restored_client:
        assert restored_client.get('/api/v1/budget-months/2026-11').json()['spent_minor']==100
        identifier=first.json()['result']['id']
        assert restored_client.get(f'/api/v1/attachments/{identifier}/content').content==png()
    with pytest.raises(FileExistsError):
        restore(destination,recovered.data_dir,'test')
    assert client.get('/api/v1/purchases').json()['items'][0]['id']==p['id']


def test_corrupt_backup_and_unsafe_manifest_rejected(client,users,settings,tmp_path):
    backup(settings,tmp_path/'snapshot')
    manifest=tmp_path/'snapshot/manifest.json'
    data=json.loads(manifest.read_text());data['files']['../outside']='invalid';manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Unsafe'):
        restore(tmp_path/'snapshot',tmp_path/'unsafe','test')
    del data['files']['../outside'];manifest.write_text(json.dumps(data))
    with (tmp_path/'snapshot/pigpen.sqlite3').open('ab') as output:output.write(b'changed')
    with pytest.raises(ValueError,match='checksum'):
        restore(tmp_path/'snapshot',tmp_path/'corrupt','test')
    assert not (tmp_path/'corrupt').exists()


def test_cli_migration_and_fresh_process_readiness(tmp_path):
    env={**os.environ,'PIGPEN_ENV':'test','PIGPEN_DATA_DIR':str(tmp_path/'cli')}
    for command in ['migrate','check']:
        result=subprocess.run([sys.executable,'-m','pigpen',command],cwd=Path(__file__).parents[1],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
