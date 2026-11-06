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


def test_localhost_server_start_stop_and_openapi(tmp_path):
    env={**os.environ,'PIGPEN_ENV':'test','PIGPEN_DATA_DIR':str(tmp_path/'server')}
    cwd=Path(__file__).parents[1]
    subprocess.run([sys.executable,'-m','pigpen','migrate'],cwd=cwd,env=env,capture_output=True,check=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','pigpen','serve','--port',str(port)],cwd=cwd,env=env,
                             stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+10
        while True:
            try:
                with urlopen(f'http://127.0.0.1:{port}/api/v1/health',timeout=1) as response:
                    assert json.load(response)=={'status':'ok'}
                break
            except URLError:
                if process.poll() is not None or time.monotonic()>deadline:
                    raise AssertionError('Server failed to become healthy')
                time.sleep(0.05)
        with urlopen(f'http://127.0.0.1:{port}/openapi.json',timeout=1) as response:
            assert '/api/v1/sync/push' in json.load(response)['paths']
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)
        if process.stderr:process.stderr.close()
