import os
import sys
import types
from fastapi.testclient import TestClient

# Stub Google BigQuery client before importing application modules
dummy = types.SimpleNamespace(
    Client=lambda *a, **k: None,
    ScalarQueryParameter=lambda *a, **k: None,
    QueryJobConfig=lambda *a, **k: None,
)
google_cloud = types.SimpleNamespace(bigquery=dummy)
sys.modules.setdefault("google", types.ModuleType("google"))
sys.modules["google.cloud"] = google_cloud
sys.modules["google.cloud.bigquery"] = dummy

# Ensure backend path and settings
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
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


client = TestClient(app)


class FakeClient:
    def __init__(self):
        self.calls = []

    def insert_rows_json(self, table_ref, rows):
        self.calls.append((table_ref, rows))
        return []


def test_import_accounts_missing_columns():
    app.dependency_overrides[get_current_user] = override_tenant_user
    original_client = bq_client.client
    bq_client.client = FakeClient()
    csv_content = "Conta,Grupo\nacc,g1\n"
    response = client.post(
        "/accounts/import?tenant_id=t1",
        files={"file": ("acc.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 400
    bq_client.client = original_client
    app.dependency_overrides.clear()


def test_import_accounts_bulk_insert():
    app.dependency_overrides[get_current_user] = override_tenant_user
    original_client = bq_client.client
    fake_client = FakeClient()
    bq_client.client = fake_client
    csv_content = "CONTA,SUBGRUPO,GRUPO\nA,S1,G1\nB,S1,G1\n"
    response = client.post(
        "/accounts/import?tenant_id=t1",
        files={"file": ("acc.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 201
    assert len(fake_client.calls) == 3
    tables = [c[0].split(".")[-1] for c in fake_client.calls]
    assert tables.count("Groups") == 1
    assert tables.count("Subgroups") == 1
    assert tables.count("Accounts") == 1
    for table, rows in fake_client.calls:
        if table.endswith("Accounts"):
            assert len(rows) == 2
    bq_client.client = original_client
    app.dependency_overrides.clear()
