from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pigpen.config import Settings, PROJECT_ROOT
from pigpen.app import create_app


def test_import_and_factory_do_not_create_database(tmp_path):
    settings = Settings(tmp_path / 'isolated', 'test')
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/v1/health').status_code == 503
    assert not settings.data_dir.exists()


@pytest.mark.parametrize('environment', ['production', 'development', 'test'])
def test_runtime_identifies_only_the_configured_environment_without_storage_side_effects(tmp_path, environment):
    settings = Settings(tmp_path / environment, environment)
    with TestClient(create_app(settings)) as client:
        response = client.get('/api/v1/runtime')
        assert response.status_code == 200
        assert response.json() == {'environment': environment}
        assert response.headers['cache-control'] == 'no-store'
        assert client.get('/api/v1/health').status_code == 503
    assert not settings.data_dir.exists()


@pytest.mark.parametrize('path', [Path('relative'), PROJECT_ROOT / 'data', PROJECT_ROOT])
def test_runtime_data_cannot_be_in_checkout(path):
    with pytest.raises(ValueError):
        Settings(path)


def test_missing_configuration_never_falls_back_to_production(monkeypatch):
    monkeypatch.delenv('PIGPEN_DATA_DIR', raising=False)
    with pytest.raises(ValueError, match='explicitly'):
        Settings.from_env()


def test_existing_file_cannot_be_configured_as_data_directory(tmp_path):
    path=tmp_path/'file';path.write_text('not a directory')
    with pytest.raises(ValueError,match='directory'):Settings(path)
