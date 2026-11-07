import base64
import stat
import pytest
from fastapi.testclient import TestClient
from pigpen.config import Settings
from pigpen.push import generate_vapid_key
from pigpen.app import create_app


def test_push_public_key_and_private_key_creation(tmp_path, client):
    assert client.get('/api/v1/push-config').json() == {'enabled': False, 'public_key': None}
    path = tmp_path / 'vapid.pem'
    generate_vapid_key(path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        generate_vapid_key(path)
    assert path.read_bytes() == original
    settings = Settings(tmp_path / 'synthetic', 'development', str(path), 'https://example.test')
    with TestClient(create_app(settings)) as configured:
        response = configured.get('/api/v1/push-config')
        data = response.json()
        assert data['enabled'] is True
        assert len(base64.urlsafe_b64decode(data['public_key']+'=')) == 65
        assert 'PRIVATE' not in response.text
        path.write_text('invalid synthetic key')
        response = configured.get('/api/v1/push-config')
        assert response.status_code == 503
        assert str(path) not in response.text
