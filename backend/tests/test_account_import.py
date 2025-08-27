import os
import sys
import types

from fastapi.testclient import TestClient

# Stub Google BigQuery client before importing application modules to avoid
# external dependencies during tests.


class FakeClient:
    def insert_rows_json(self, *a, **k):
        return []


fake_bigquery = types.SimpleNamespace(
    Client=lambda *a, **k: FakeClient(),
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


def override_tenant_user():
    return UserInDB(
        id="u1",
        username="tenant",
        email="t@example.com",
        hashed_password="",
        role=Role.tenant_user,
        tenant_id="t1",
    )


client = TestClient(app)


def test_import_accounts_reports_skipped_rows():
    app.dependency_overrides[get_current_user] = override_tenant_user
    payload = [
        {"subgroup_id": "s1", "name": "valid", "balance": 0, "tenant_id": "t1"},
        {"subgroup_id": "", "name": "missing subgroup", "balance": 0, "tenant_id": "t1"},
        {"subgroup_id": "s2", "name": "", "balance": 0, "tenant_id": "t1"},
    ]
    response = client.post("/accounts/import?tenant_id=t1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 1
    assert data["skipped"] == 2
    assert data["skipped_details"] == [
        {"row": 2, "reason": "blank fields: subgroup_id"},
        {"row": 3, "reason": "blank fields: name"},
    ]
    app.dependency_overrides.clear()
