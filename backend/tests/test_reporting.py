import sys
from pathlib import Path

import asyncio
import importlib
import types

# Add backend directory to sys.path to import app package
sys.path.append(str(Path(__file__).resolve().parents[1]))


def _load_service_with_query(sample):
    async def fake_query(table, filters):
        return sample

    fake_module = types.SimpleNamespace(query=fake_query)
    sys.modules["app.db.bq_client"] = fake_module

    module = importlib.reload(importlib.import_module("app.services.reporting"))
    return module.cash_flow_summary


def test_cash_flow_summary_group_by_month():
    sample = [
        {"date": "2025-01-01", "predicted": 100, "realized": 90},
        {"date": "2025-01-15", "predicted": 200, "realized": 180},
        {"date": "2025-02-01", "predicted": 150, "realized": 120},
    ]

    cash_flow_summary = _load_service_with_query(sample)
    result = asyncio.run(cash_flow_summary("month"))
    assert result == [
        {"period": "2025-01", "predicted": 300.0, "realized": 270.0},
        {"period": "2025-02", "predicted": 150.0, "realized": 120.0},
    ]


def test_cash_flow_summary_group_by_day():
    sample = [
        {"date": "2025-01-01", "predicted": 100, "realized": 90},
        {"date": "2025-01-15", "predicted": 200, "realized": 180},
        {"date": "2025-02-01", "predicted": 150, "realized": 120},
    ]

    cash_flow_summary = _load_service_with_query(sample)
    result = asyncio.run(cash_flow_summary("day"))
    assert result == [
        {"period": "2025-01-01", "predicted": 100.0, "realized": 90.0},
        {"period": "2025-01-15", "predicted": 200.0, "realized": 180.0},
        {"period": "2025-02-01", "predicted": 150.0, "realized": 120.0},
    ]
