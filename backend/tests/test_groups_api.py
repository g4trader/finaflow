import os
import sys
import types

import pytest
from fastapi.testclient import TestClient

# Stub Google BigQuery client before importing application modules to avoid
# external dependencies during tests.
fake_bigquery = types.SimpleNamespace(
    Client=lambda *a, **k: None,
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
os.environ.setdefault("PROJECT_ID", "test-project")
os.environ.setdefault("DATASET", "test-dataset")

from app.main import app  # noqa: E402
from app.models.user import Role, UserInDB  # noqa: E402
from app.services.dependencies import get_current_user  # noqa: E402
import app.api.groups as groups_api  # noqa: E402

client = TestClient(app)


def override_tenant_user():
    return UserInDB(
        id="u1",
        username="tenant",
        email="t@example.com",
        hashed_password="",
        role=Role.tenant_user,
        tenant_id="t1",
    )


def override_super_admin():
    return UserInDB(
        id="u2",
        username="admin",
        email="a@example.com",
        hashed_password="",
        role=Role.super_admin,
        tenant_id=None,
    )


def test_group_update_forbidden_for_other_tenant(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user

    def fake_query(table, filters):
        return [
            {
                "id": "g1",
                "name": "g",
                "description": None,
                "tenant_id": "t2",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

    monkeypatch.setattr(groups_api, "query", fake_query)

    response = client.put(
        "/groups/g1",
        json={"name": "new", "description": None, "tenant_id": "t2"},
    )
    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_group_update_success_super_admin(monkeypatch):
    app.dependency_overrides[get_current_user] = override_super_admin

    def fake_query(table, filters):
        return [
            {
                "id": "g1",
                "name": "old",
                "description": None,
                "tenant_id": "t1",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

    updates = {}

    def fake_update(table, id, data):
        updates["args"] = (table, id, data)

    monkeypatch.setattr(groups_api, "query", fake_query)
    monkeypatch.setattr(groups_api, "update", fake_update)

    response = client.put(
        "/groups/g1",
        json={"name": "new", "description": None, "tenant_id": "t1"},
    )
    assert response.status_code == 200
    assert updates["args"] == (
        "Groups",
        "g1",
        {"name": "new", "description": None, "tenant_id": "t1"},
    )
    assert response.json()["name"] == "new"

    app.dependency_overrides.clear()


def test_group_delete_forbidden_for_other_tenant(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user

    def fake_query(table, filters):
        return [
            {
                "id": "g1",
                "name": "g",
                "description": None,
                "tenant_id": "t2",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

    monkeypatch.setattr(groups_api, "query", fake_query)

    response = client.delete("/groups/g1")
    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_group_delete_success_super_admin(monkeypatch):
    app.dependency_overrides[get_current_user] = override_super_admin

    def fake_query(table, filters):
        return [
            {
                "id": "g1",
                "name": "g",
                "description": None,
                "tenant_id": "t1",
                "created_at": "2024-01-01T00:00:00",
            }
        ]

    calls = {}

    def fake_delete(table, id):
        calls["args"] = (table, id)

    monkeypatch.setattr(groups_api, "query", fake_query)
    monkeypatch.setattr(groups_api, "delete", fake_delete)

    response = client.delete("/groups/g1")
    assert response.status_code == 204
    assert calls["args"] == ("Groups", "g1")

    app.dependency_overrides.clear()
