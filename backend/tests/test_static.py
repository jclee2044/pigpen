from fastapi.testclient import TestClient
import pytest
from pigpen.app import create_app
from pigpen.config import Settings
from pigpen.database import migrate


def test_app_shell_keeps_api_and_private_data_separate(tmp_path):
    static = tmp_path / 'dist'
    static.mkdir()
    (static / 'index.html').write_text('<html>PigPen shell</html>')
    (static / 'sw.js').write_text('/* worker */')
    (static / 'assets').mkdir()
    (static / 'assets/app-hash.js').write_text('/* bundle */')
    settings = Settings(tmp_path / 'private', 'test', static_dir=static)
    migrate(settings)
    (settings.data_dir / 'secret.txt').write_text('private financials')
    # Even an accidental static symlink cannot expose private files.
    (static / 'leak.txt').symlink_to(settings.data_dir / 'secret.txt')
    with TestClient(create_app(settings)) as client:
        for route in ['/', '/purchases', '/approvals/unknown']:
            response = client.get(route)
            assert response.status_code == 200
            assert 'PigPen shell' in response.text
            assert response.headers['cache-control'] == 'no-cache'
        assert client.get('/api/v1/health').json() == {'status': 'ok'}
        assert client.get('/api/unknown').status_code == 404
        for route in ['/missing.js', '/leak.txt', '/secret.txt', '/%2e%2e/private/secret.txt']:
            assert client.get(route).status_code == 404
        assert client.get('/sw.js').headers['cache-control'] == 'no-cache'
        assert client.get('/sw.js').headers['service-worker-allowed'] == '/'
        assert 'immutable' in client.get('/assets/app-hash.js').headers['cache-control']


def test_static_private_overlap_is_rejected(tmp_path):
    (tmp_path / 'index.html').write_text('shell')
    with pytest.raises(ValueError, match='separate'):
        Settings(tmp_path / 'private', 'test', static_dir=tmp_path)
    with pytest.raises(ValueError, match='separate'):
        Settings(tmp_path, 'test', static_dir=tmp_path)
