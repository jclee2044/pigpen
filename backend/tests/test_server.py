"""Exercise the actual ASGI server in a fresh process with disposable synthetic storage."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError
import json
from contextlib import contextmanager
from urllib.request import Request
from conftest import operation
from pigpen.recovery import restore


def server_environment(directory):
    # Never inherit installed database, static or push settings into test servers.
    return {**{key:value for key,value in os.environ.items() if not key.startswith('PIGPEN_')},
            'PIGPEN_ENV':'test','PIGPEN_DATA_DIR':str(directory)}


def request_json(origin, path, payload=None):
    request=Request(origin+path, data=json.dumps(payload).encode() if payload else None,
                    headers={'Content-Type':'application/json'})
    with urlopen(request,timeout=3) as response:
        return json.load(response)


@contextmanager
def running_server(env):
    cwd=Path(__file__).parents[1]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    origin=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','pigpen','serve','--port',str(port)],cwd=cwd,env=env,
                             stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+10
        while True:
            try:
                with urlopen(origin+'/api/v1/health',timeout=1) as response:
                    assert json.load(response)=={'status':'ok'}
                break
            except URLError:
                if process.poll() is not None or time.monotonic()>deadline:
                    raise AssertionError('Server failed to become healthy')
                time.sleep(0.05)
        yield origin
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)
        if process.stderr:process.stderr.close()


def migrate_environment(env):
    subprocess.run([sys.executable,'-m','pigpen','migrate'],cwd=Path(__file__).parents[1],
                   env=env,capture_output=True,check=True)


def test_localhost_server_start_stop_and_openapi(tmp_path):
    env=server_environment(tmp_path/'server')
    migrate_environment(env)
    with running_server(env) as origin:
        assert '/api/v1/sync/push' in request_json(origin,'/openapi.json')['paths']
        assert request_json(origin,'/api/v1/runtime')=={'environment':'test'}


def test_financials_and_operation_replay_survive_process_restart_and_backup_restore(tmp_path):
    env=server_environment(tmp_path/'persistent-server')
    migrate_environment(env)
    with running_server(env) as origin:
        request_json(origin,'/api/v1/operations',operation('household.initialize',{'name':'Synthetic restart household'}))
        actor=request_json(origin,'/api/v1/operations',operation('user.create',{'name':'Restart actor'}))['result']['id']
        categories=request_json(origin,'/api/v1/categories')['items']
        food=next(category['id'] for category in categories if category['name']=='Food')
        request_json(origin,'/api/v1/operations',operation('budget.set',{
            'month':'2025-11','expected_income_minor':100000,
            'allocations':[{'category_id':food,'amount_minor':5000}]},actor))
        saved=operation('purchase.create',{'item':'Persisted synthetic groceries','amount_minor':2900,
            'category_id':food,'transaction_date':'2025-11-01'},actor)
        original=request_json(origin,'/api/v1/operations',saved)
        assert request_json(origin,'/api/v1/budget-months/2025-11')['spent_minor']==2900
    with running_server(env) as origin:
        assert request_json(origin,'/api/v1/operations',saved)==original
        assert len(request_json(origin,'/api/v1/purchases')['items'])==1
        assert request_json(origin,'/api/v1/budget-months/2025-11')['allocated_minor']==5000
    snapshot=tmp_path/'snapshot'
    subprocess.run([sys.executable,'-m','pigpen','backup',str(snapshot)],cwd=Path(__file__).parents[1],
                   env=env,capture_output=True,check=True)
    recovered=restore(snapshot,tmp_path/'recovered','test')
    with running_server(server_environment(recovered.data_dir)) as origin:
        assert request_json(origin,'/api/v1/budget-months/2025-11')['spent_minor']==2900
        assert request_json(origin,'/api/v1/operations',saved)==original
        assert len(request_json(origin,'/api/v1/purchases')['items'])==1
