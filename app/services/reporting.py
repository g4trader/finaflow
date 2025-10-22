"""Utilities for reporting related queries backed by PostgreSQL."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

import asyncio
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.financial import CashFlow


async def cash_flow_summary(group_by: str, tenant_id: str) -> Any:
    """Return cash-flow aggregates grouped by the provided period."""

    if group_by not in {"month", "day"}:
        raise ValueError("group_by must be 'month' or 'day'")

    return await asyncio.to_thread(_calculate_cash_flow, group_by, tenant_id)


def _calculate_cash_flow(group_by: str, tenant_id: str) -> List[Dict[str, float]]:
    """Fetch cash-flow data from the relational database and aggregate it."""

    with SessionLocal() as session:  # type: Session
        rows = (
            session.query(CashFlow)
            .filter(CashFlow.tenant_id == tenant_id)
            .order_by(CashFlow.date)
            .all()
        )

    totals: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"predicted": 0.0, "realized": 0.0}
    )

    for row in rows:
        dt: datetime = row.date
        key = dt.strftime("%Y-%m-%d" if group_by == "day" else "%Y-%m")

        totals[key]["predicted"] += float(row.total_revenue or 0)
        totals[key]["realized"] += float(row.total_expenses or 0)

    return [
        {"period": period, **values}
        for period, values in sorted(totals.items())
    ]
