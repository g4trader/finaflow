from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List

from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig

from app.config import Settings

logger = logging.getLogger(__name__)


class _DummyBigQueryClient:
    def insert_rows_json(self, table, rows):
        return []

    def query(self, sql, job_config=None):
        class _Job:
            def result(self_inner):
                return []

        return _Job()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_client():
    settings = get_settings()
    if settings.PROJECT_ID and settings.DATASET:
        try:
            client = bigquery.Client(project=settings.PROJECT_ID)
            if client is None:  # pragma: no cover - handle stubs returning None
                raise RuntimeError("BigQuery client returned None")
            return client
        except Exception as e:  # pragma: no cover - fallback when client fails
            logger.warning("Falling back to dummy BigQuery client: %s", e)
    else:  # pragma: no cover - missing configuration
        logger.warning(
            "BigQuery configuration incomplete; using dummy client"
        )
    return _DummyBigQueryClient()


class _ClientProxy:
    def __getattr__(self, name):
        return getattr(get_client(), name)

    def __setattr__(self, name, value):
        setattr(get_client(), name, value)


client = _ClientProxy()


def _format_table(settings: Settings, table: str, quoted: bool = True) -> str:
    project = settings.PROJECT_ID or ""
    dataset = settings.DATASET or ""
    if project and dataset:
        if quoted:
            return f"`{project}.{dataset}.{table}`"
        return f"{project}.{dataset}.{table}"
    return table


def query(table: str, filters: Dict[str, Any]) -> List[Dict]:
    """Executa ``SELECT *`` com filtros opcionais."""
    settings = get_settings()
    client = get_client()
    table_ref = _format_table(settings, table)
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
    settings = get_settings()
    client = get_client()
    table_ref = _format_table(settings, table, quoted=False)
    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        raise RuntimeError(f"Error inserting into {table}: {errors}")


def insert_many(table: str, rows: List[Dict[str, Any]]):
    """Insert multiple JSON rows into the specified table.

    Raises:
        RuntimeError: If BigQuery reports any insertion errors.
    """
    settings = get_settings()
    client = get_client()
    table_ref = _format_table(settings, table, quoted=False)
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"Error inserting into {table}: {errors}")


def update(table: str, id: str, data: Dict[str, Any]):
    """Atualiza uma linha por ``id`` na tabela especificada."""
    settings = get_settings()
    client = get_client()
    set_clause = ", ".join([f"{k}=@{k}" for k in data.keys()])
    table_ref = _format_table(settings, table)
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
    settings = get_settings()
    client = get_client()
    table_ref = _format_table(settings, table)
    sql = f"DELETE FROM {table_ref} WHERE id=@id"
    job_config = QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", id)]
    )
    client.query(sql, job_config=job_config).result()


def query_user(username: str):
    """Busca usuário por ``username`` na tabela ``Users``."""
    return query("Users", {"username": username})

