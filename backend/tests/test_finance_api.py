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
import app.api.reports as reports_api  # noqa: E402
import app.api.transactions as transactions_api  # noqa: E402
import app.api.forecast as forecast_api  # noqa: E402


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


def test_cash_flow_endpoint_isolates_tenant(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user

    recorded = {}

    async def fake_cash_flow_summary(group_by, tenant_id):
        recorded["group_by"] = group_by
        recorded["tenant_id"] = tenant_id
        return [{"period": "2025-01", "predicted": 100.0, "realized": 90.0}]

    monkeypatch.setattr(reports_api, "cash_flow_summary", fake_cash_flow_summary)

    response = client.get("/reports/cash-flow")
    assert response.status_code == 200
    assert recorded == {"group_by": "month", "tenant_id": "t1"}
    assert response.json() == [
        {"period": "2025-01", "predicted": 100.0, "realized": 90.0}
    ]
    app.dependency_overrides.clear()


def test_transactions_list_isolates_tenant(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user
    sample = [
        {
            "id": "tx1",
            "account_id": "a1",
            "amount": 10.0,
            "tenant_id": "t1",
            "created_at": "2025-01-01T00:00:00",
        },
        {
            "id": "tx2",
            "account_id": "a2",
            "amount": 20.0,
            "tenant_id": "t2",
            "created_at": "2025-01-02T00:00:00",
        },
    ]
    recorded = {}

    def fake_query(table, filters):
        recorded["filters"] = filters
        return [row for row in sample if row["tenant_id"] == filters["tenant_id"]]

    monkeypatch.setattr(transactions_api, "query", fake_query)

    response = client.get("/transactions?tenant_id=t1")
    assert response.status_code == 200
    assert recorded["filters"] == {"tenant_id": "t1"}
    assert response.json() == [
        {
            "id": "tx1",
            "account_id": "a1",
            "amount": "10.0",
            "description": None,
            "tenant_id": "t1",
            "created_at": "2025-01-01T00:00:00",
        }
    ]
    app.dependency_overrides.clear()


def test_forecast_list_isolates_tenant(monkeypatch):
    app.dependency_overrides[get_current_user] = override_tenant_user
    sample = [
        {
            "id": "f1",
            "account_id": "a1",
            "amount": 5.0,
            "tenant_id": "t1",
            "created_at": "2025-01-01T00:00:00",
        },
        {
            "id": "f2",
            "account_id": "a2",
            "amount": 7.0,
            "tenant_id": "t2",
            "created_at": "2025-01-02T00:00:00",
        },
    ]
    recorded = {}

    def fake_query(table, filters):
        recorded["filters"] = filters
        return [row for row in sample if row["tenant_id"] == filters["tenant_id"]]

    monkeypatch.setattr(forecast_api, "query", fake_query)

    response = client.get("/forecast?tenant_id=t1")
    assert response.status_code == 200
    assert recorded["filters"] == {"tenant_id": "t1"}
    assert response.json() == [
        {
            "id": "f1",
            "account_id": "a1",
            "amount": "5.0",
            "description": None,
            "tenant_id": "t1",
            "created_at": "2025-01-01T00:00:00",
        }
    ]
    app.dependency_overrides.clear()

