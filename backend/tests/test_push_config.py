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


@pytest.mark.parametrize('subject', ['https://example.test:8445', 'https://example.test:8445/push/contact', 'mailto:admin@example.test'])
def test_encrypted_push_with_contact_uri(tmp_path, monkeypatch, subject):
    import json
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid
    from requests import Response, Session
    from pigpen.push import send_webpush
    path=tmp_path/'vapid.pem'
    generate_vapid_key(path)
    settings=Settings(tmp_path/'synthetic','development',str(path),subject)
    public=ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
        serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
    subscription={'endpoint':'https://web.push.apple.com/synthetic',
        'p256dh':base64.urlsafe_b64encode(public).decode().rstrip('='),
        'auth':base64.urlsafe_b64encode(b'A'*16).decode().rstrip('=')}
    calls=[]
    def transport(self,method,url,**kwargs):
        calls.append(url)
        assert kwargs['allow_redirects'] is False
        assert kwargs['headers']['ttl']=='86400'
        assert kwargs['headers']['content-encoding']=='aes128gcm'
        assert isinstance(kwargs['data'],bytes) and len(kwargs['data'])>30
        authorization=kwargs['headers']['Authorization']
        assert Vapid.verify(authorization)
        token=authorization.split('t=',1)[1].split(',',1)[0]
        encoded=token.split('.')[1]
        claims=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        assert claims['sub']==subject
        assert claims['aud']=='https://web.push.apple.com'
        response=Response();response.status_code=201
        return response
    monkeypatch.setattr(Session,'request',transport)
    assert send_webpush(settings,subscription,{'notification_id':'synthetic'})==201
    assert calls==[subscription['endpoint']]


@pytest.mark.parametrize('subject', ['https://example.test:invalid', 'https://user:secret@example.test', 'http://example.test', 'https://', 'mailto:', 'https://example.test/\nsecret'])
def test_invalid_contact_configuration_is_not_advertised(tmp_path, subject):
    from pigpen.push import push_config
    from pigpen.errors import DomainError
    path=tmp_path/'vapid.pem';generate_vapid_key(path)
    settings=Settings(tmp_path/'synthetic','development',str(path),subject)
    with pytest.raises(DomainError,match='Push configuration is unavailable'):
        push_config(settings)
