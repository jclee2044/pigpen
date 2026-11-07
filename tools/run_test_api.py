"""Disposable synthetic API for browser tests. Never reads production configuration."""
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from pigpen.config import Settings
from pigpen.database import migrate
from pigpen.app import create_app
import uvicorn
with tempfile.TemporaryDirectory(prefix='pigpen-browser-test-') as directory:
    settings=Settings(Path(directory),'test')
    migrate(settings)
    uvicorn.run(create_app(settings),host='127.0.0.1',port=8765,log_level='warning')
