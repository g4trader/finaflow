from datetime import datetime
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.models.finance import TransactionCreate, ForecastCreate


def test_transaction_date_parsing_and_serialization():
    data = {
        "account_id": "acc1",
        "amount": 10.5,
        "date": "2024-05-20",
        "tenant_id": "tenant1",
        "created_at": "2024-05-01T12:30:45",
    }
    tx = TransactionCreate(**data)
    assert tx.date.year == 2024
    assert tx.created_at.year == 2024
    dumped = tx.model_dump(mode="json")
    assert dumped["date"] == "2024-05-20"
    assert dumped["created_at"].startswith("2024-05-01T12:30:45")


def test_forecast_date_parsing_and_serialization():
    data = {
        "account_id": "acc1",
        "amount": 20.0,
        "expected_date": "2024-06-15",
        "tenant_id": "tenant1",
        "created_at": "2024-06-01T08:00:00",
    }
    fc = ForecastCreate(**data)
    assert fc.expected_date.month == 6
    assert fc.created_at.hour == 8
    dumped = fc.model_dump(mode="json")
    assert dumped["expected_date"] == "2024-06-15"
    assert dumped["created_at"].startswith("2024-06-01T08:00:00")


def test_invalid_transaction_date():
    data = {
        "account_id": "acc1",
        "amount": 10.5,
        "date": "invalid-date",
        "tenant_id": "tenant1",
        "created_at": "2024-05-01T12:30:45",
    }
    with pytest.raises(ValueError):
        TransactionCreate(**data)
