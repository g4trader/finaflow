from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from typing import Any, Dict, List

from app.config import Settings

settings = Settings()


class _DummyBigQueryClient:
    def insert_rows_json(self, table, rows):
        return []

    def query(self, sql, job_config=None):
        class _Job:
            def result(self_inner):
                return []

        return _Job()


try:
    client = bigquery.Client(project=settings.PROJECT_ID)
    if client is None:
        client = _DummyBigQueryClient()
except Exception:
    client = _DummyBigQueryClient()


def query(table: str, filters: Dict[str, Any]) -> List[Dict]:
    """Executa ``SELECT *`` com filtros opcionais."""
    table_ref = f"`{settings.PROJECT_ID}.{settings.DATASET}.{table}`"
    sql = f"SELECT * FROM {table_ref}"
    params = []
    if filters:
        wheres = []
        for k, v in filters.items():
            wheres.append(f"{k}=@{k}")
            params.append(bigquery.ScalarQueryParameter(k, "STRING", v))
        sql += " WHERE " + " AND ".join(wheres)

    job = client.query(sql, job_config=QueryJobConfig(query_parameters=params))
    rows = job.result()
    return [dict(row) for row in rows]


def insert(table: str, row: Dict[str, Any]):
    """Insere uma linha JSON na tabela especificada."""
    table_ref = f"{settings.PROJECT_ID}.{settings.DATASET}.{table}"
    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        raise RuntimeError(f"Error inserting into {table}: {errors}")


def insert_many(table: str, rows: List[Dict[str, Any]]):
    """Insert multiple JSON rows into the specified table.

    Raises:
        RuntimeError: If BigQuery reports any insertion errors.
    """
    table_ref = f"{settings.PROJECT_ID}.{settings.DATASET}.{table}"
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"Error inserting into {table}: {errors}")


def update(table: str, id: str, data: Dict[str, Any]):
    """Atualiza uma linha por ``id`` na tabela especificada."""
    set_clause = ", ".join([f"{k}=@{k}" for k in data.keys()])
    table_ref = f"`{settings.PROJECT_ID}.{settings.DATASET}.{table}`"
    sql = f"""
UPDATE {table_ref}
SET {set_clause}
WHERE id=@id
"""
    params = [bigquery.ScalarQueryParameter("id", "STRING", id)]
    for k, v in data.items():
        params.append(bigquery.ScalarQueryParameter(k, "STRING", v))
    client.query(sql, job_config=QueryJobConfig(query_parameters=params)).result()


def delete(table: str, id: str):
    """Deleta uma linha por ``id`` na tabela especificada."""
    table_ref = f"`{settings.PROJECT_ID}.{settings.DATASET}.{table}`"
    sql = f"DELETE FROM {table_ref} WHERE id=@id"
    job_config = QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", id)]
    )
    client.query(sql, job_config=job_config).result()


def query_user(username: str):
    """Busca usuário por ``username`` na tabela ``Users``."""
    return query("Users", {"username": username})
