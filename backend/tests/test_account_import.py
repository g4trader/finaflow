import os
import sys
import types

from fastapi.testclient import TestClient


class DummyClient:
    def insert_rows_json(self, table, rows):
        return []


fake_bigquery = types.SimpleNamespace(
    Client=lambda *a, **k: DummyClient(),
    ScalarQueryParameter=lambda *a, **k: None,
    QueryJobConfig=lambda *a, **k: None,
)
google_cloud = types.SimpleNamespace(bigquery=fake_bigquery)
sys.modules.setdefault("google", types.ModuleType("google"))
sys.modules["google.cloud"] = google_cloud
sys.modules["google.cloud.bigquery"] = fake_bigquery

# Ensure the "backend" directory is on the Python path so ``app`` can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Provide required configuration variables for Settings
os.environ.setdefault("JWT_SECRET", "testing-secret")

from app.main import app  # noqa: E402
from app.models.user import Role, UserInDB  # noqa: E402
from app.services.dependencies import get_current_user  # noqa: E402
from app.db import bq_client  # noqa: E402


def override_tenant_user():
    return UserInDB(
        id="u1",
        username="tenant",
        email="t@example.com",
        hashed_password="",
        role=Role.tenant_user,
        tenant_id="t1",
    )


client = TestClient(app, raise_server_exceptions=False)


def test_import_accounts_failure(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user

    calls = {"count": 0}

    def failing_insert_rows_json(table, rows):
        calls["count"] += 1
        return [{"error": "bad"}]

    monkeypatch.setattr(bq_client.client, "insert_rows_json", failing_insert_rows_json)

    payload = [
        {"subgroup_id": "sg1", "name": "acc1", "balance": 0, "tenant_id": "t1"}
    ]

    response = client.post("/accounts/import?tenant_id=t1", json=payload)
    assert response.status_code == 500
    assert calls["count"] == 1

    app.dependency_overrides.clear()


def test_import_accounts_success(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user

    calls = {"count": 0}

    def tracking_insert_rows_json(table, rows):
        calls["count"] += 1
        return []

    monkeypatch.setattr(bq_client.client, "insert_rows_json", tracking_insert_rows_json)

    payload = [
        {"subgroup_id": "sg1", "name": "acc1", "balance": 0, "tenant_id": "t1"}
    ]

    response = client.post("/accounts/import?tenant_id=t1", json=payload)
    assert response.status_code == 201
    assert calls["count"] == 1

    app.dependency_overrides.clear()
