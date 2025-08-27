from typing import Literal, List, Dict
from app.db.bq_client import PROJECT_ID, DATASET, client

CASH_FLOW_TABLE = "CashFlow"

async def cash_flow_summary(group_by: Literal["month", "day"] = "month") -> List[Dict]:
    """Aggregate cash flow data from BigQuery.

    Args:
        group_by: "month" or "day" defining the aggregation granularity.

    Returns:
        List of dictionaries with period, predicted and realized totals.
    """
    group_expr = "DATE(date)" if group_by == "day" else "FORMAT_DATE('%Y-%m', DATE(date))"
    table = f"`{PROJECT_ID}.{DATASET}.{CASH_FLOW_TABLE}`"
    sql = f"""
        SELECT {group_expr} AS period,
               SUM(predicted) AS predicted,
               SUM(realized) AS realized
        FROM {table}
        GROUP BY period
        ORDER BY period
    """
    job = client.query(sql)
    rows = job.result()
    return [dict(row) for row in rows]
