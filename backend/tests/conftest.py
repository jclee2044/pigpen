from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pigpen.app import create_app
from pigpen.config import Settings
from pigpen.database import Database, migrate


@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path / 'household-test', 'test')


@pytest.fixture
def client(settings):
    migrate(settings)
    with TestClient(create_app(settings)) as c:
        yield c


def operation(kind, data, actor=None, entity=None):
    return dict(operation_id=str(uuid4()), entity_id=entity or str(uuid4()), actor_id=actor,
                client_time=datetime.now(timezone.utc).isoformat(), kind=kind, data=data)


def submit(client, kind, data, actor=None, entity=None):
    response = client.post('/api/v1/operations', json=operation(kind, data, actor, entity))
    assert response.status_code == 200, response.text
    return response.json()['result']


@pytest.fixture
def household(client):
    return submit(client, 'household.initialize', {'name': 'Synthetic household'})


@pytest.fixture
def users(client, household):
    return [submit(client, 'user.create', {'name': name}) for name in ['Alex', 'Sam', 'Jo']]
