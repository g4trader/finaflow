import os
import sys
import types

import pytest
from fastapi.testclient import TestClient


class DummyClient:
    def insert_rows_json(self, table, rows):
        return []


# Ensure the "backend" directory is on the Python path so ``app`` can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Provide required configuration variables for Settings
os.environ.setdefault("JWT_SECRET", "testing-secret")
os.environ.setdefault("PROJECT_ID", "test-project")
os.environ.setdefault("DATASET", "test-dataset")

from app.models.user import Role, UserInDB  # noqa: E402
from app.services.dependencies import get_current_user  # noqa: E402
from app.models.finance import AccountImportSummary  # noqa: E402


def override_tenant_user():
    return UserInDB(
        id="u1",
        username="tenant",
        email="t@example.com",
        hashed_password="",
        role=Role.tenant_user,
        tenant_id="t1",
    )


@pytest.fixture
def client_with_bq(monkeypatch):
    fake_bigquery = types.SimpleNamespace(
        Client=lambda *a, **k: DummyClient(),
        ScalarQueryParameter=lambda *a, **k: None,
        QueryJobConfig=lambda *a, **k: None,
    )
    google_cloud = types.SimpleNamespace(bigquery=fake_bigquery)
    monkeypatch.setitem(sys.modules, "google", types.ModuleType("google"))
    monkeypatch.setitem(sys.modules, "google.cloud", google_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", fake_bigquery)

    from app.main import app  # noqa: E402
    from app.db import bq_client  # noqa: E402

    client = TestClient(app, raise_server_exceptions=False)
    yield app, client, bq_client


def test_import_accounts_failure(client_with_bq, monkeypatch):
    app, client, bq_client = client_with_bq
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


def test_import_accounts_success(client_with_bq, monkeypatch):
    app, client, bq_client = client_with_bq
    app.dependency_overrides[get_current_user] = override_tenant_user

    calls = {"count": 0}

    def tracking_insert_rows_json(table, rows):
        calls["count"] += 1
        return []

    monkeypatch.setattr(bq_client.client, "insert_rows_json", tracking_insert_rows_json)

    payload = [
        {"subgroup_id": "sg1", "name": "acc1", "balance": 0, "tenant_id": "t1"},
        {
            "subgroup_id": "sg1",
            "name": "acc2",
            "balance": "not-a-number",
            "tenant_id": "t1",
        },
    ]

    response = client.post("/accounts/import?tenant_id=t1", json=payload)
    assert response.status_code == 201
    assert calls["count"] == 1
    summary = AccountImportSummary(**response.json())
    assert summary.skipped == [{"row": 1, "reason": "invalid balance"}]
    assert len(summary.inserted) == 1

    app.dependency_overrides.clear()
