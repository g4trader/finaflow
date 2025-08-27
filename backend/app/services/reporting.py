"""Utilities for reporting related queries."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from app.db.bq_client import query

CASH_FLOW_TABLE = "CashFlow"


async def cash_flow_summary(group_by: str) -> Any:
    """Return cash-flow aggregates grouped by the provided period.

    The function fetches cash-flow records from the database and groups them
    by either ``month`` or ``day``. Each group contains the sum of the
    ``predicted`` and ``realized`` values.

    Args:
        group_by: ``"month"`` or ``"day"`` defining aggregation granularity.

    Returns:
        A list of dictionaries with ``period``, ``predicted`` and ``realized``
        totals ordered by the period.
    """

    rows = await query(CASH_FLOW_TABLE, {})

    totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"predicted": 0.0, "realized": 0.0})

    for row in rows:
        dt = datetime.fromisoformat(str(row["date"]))
        if group_by == "day":
            key = dt.strftime("%Y-%m-%d")
        elif group_by == "month":
            key = dt.strftime("%Y-%m")
        else:
            raise ValueError("group_by must be 'month' or 'day'")

        totals[key]["predicted"] += float(row.get("predicted", 0))
        totals[key]["realized"] += float(row.get("realized", 0))

    return [
        {"period": period, **values}
        for period, values in sorted(totals.items())
    ]
