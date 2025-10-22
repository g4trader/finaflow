import os
import sys
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, create_tables, drop_tables  # noqa: E402
from app.main import app  # noqa: E402
from app.models.auth import Tenant, User, UserRole, UserStatus  # noqa: E402
from app.models.financial import Account, AccountGroup, AccountSubgroup  # noqa: E402
from app.services.dependencies import get_current_active_user  # noqa: E402


def setup_module(module):
    """Ensure a clean database for the tests."""

    drop_tables()
    create_tables()


def _seed_database():
    session = SessionLocal()
    try:
        tenant = Tenant(name="Tenant Test", domain="tenant.test")
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        group = AccountGroup(
            tenant_id=tenant.id,
            name="Receitas",
            code="GRP-001",
        )
        session.add(group)
        session.commit()
        session.refresh(group)

        subgroup = AccountSubgroup(
            tenant_id=tenant.id,
            group_id=group.id,
            name="Serviços",
            code="SUB-001",
        )
        session.add(subgroup)
        session.commit()
        session.refresh(subgroup)

        account = Account(
            tenant_id=tenant.id,
            subgroup_id=subgroup.id,
            name="Consultoria",
            code="ACC-001",
            account_type="revenue",
        )
        session.add(account)

        user = User(
            tenant_id=tenant.id,
            username="tester",
            email="tester@example.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="User",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        session.commit()
        session.refresh(account)
        session.refresh(user)

        tenant_data = SimpleNamespace(id=tenant.id)
        account_data = SimpleNamespace(id=account.id)
        user_data = SimpleNamespace(
            id=user.id,
            tenant_id=tenant.id,
            role=user.role,
            business_unit_id=None,
            department_id=None,
        )

        return tenant_data, account_data, user_data
    finally:
        session.close()


def test_transaction_crud_flow():
    tenant, account, user = _seed_database()

    app.dependency_overrides[get_current_active_user] = lambda: user

    client = TestClient(app)

    payload = {
        "tenant_id": tenant.id,
        "account_id": account.id,
        "transaction_date": datetime.now(UTC).isoformat(),
        "description": "Venda de consultoria",
        "amount": 1500.75,
        "transaction_type": "credit",
        "category": "Serviços",
        "is_recurring": False,
        "is_forecast": False,
    }

    create_response = client.post("/transactions/", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["tenant_id"] == tenant.id
    assert created["account_id"] == account.id
    assert float(created["amount"]) == 1500.75
    assert created["created_by"] == user.id

    list_response = client.get("/transactions/")
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) == 1
    assert data[0]["id"] == created["id"]

    app.dependency_overrides.clear()
