import os
import sys
import types

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


def test_subgroup_creation_forbidden_for_other_tenant():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/subgroups/?tenant_id=t2",
        json={"group_id": "g1", "name": "s1", "tenant_id": "t2"},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_account_delete_forbidden_for_other_tenant():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.delete("/accounts/a1?tenant_id=t2")
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_account_creation_validation_error():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/accounts/?tenant_id=t1",
        json={"subgroup_id": "s1", "balance": 10.0, "tenant_id": "t1"},
    )
    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_account_creation_respects_balance():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/accounts/?tenant_id=t1",
        json={"subgroup_id": "s1", "name": "acc1", "balance": 123.45, "tenant_id": "t1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["balance"]) == 123.45
    app.dependency_overrides.clear()


def test_transaction_creation_forbidden_for_other_tenant():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/transactions/?tenant_id=t2",
        json={"account_id": "a1", "amount": 10.0, "tenant_id": "t2"},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_transaction_creation_validation_error():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/transactions/?tenant_id=t1",
        json={"amount": 10.0, "tenant_id": "t1"},
    )
    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_forecast_creation_forbidden_for_other_tenant():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/forecast/?tenant_id=t2",
        json={"account_id": "a1", "amount": 5.0, "tenant_id": "t2"},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_forecast_creation_validation_error():
    app.dependency_overrides[get_current_user] = override_tenant_user
    response = client.post(
        "/forecast/?tenant_id=t1",
        json={"account_id": "a1", "tenant_id": "t1"},
    )
    assert response.status_code == 422
    app.dependency_overrides.clear()

