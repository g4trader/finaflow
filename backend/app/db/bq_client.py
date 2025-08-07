from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from typing import Any, Dict, List

# Configurar projeto e dataset
PROJECT_ID = "automatizar-452311"
DATASET = "finaflow"
client = bigquery.Client(project=PROJECT_ID)

async def query(table: str, filters: Dict[str, Any]) -> List[Dict]:
    # Executa SELECT * FROM `PROJECT_ID.DATASET.table` com filtros opcionais.
    table_ref = f"`{PROJECT_ID}.{DATASET}.{table}`"
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

async def insert(table: str, row: Dict[str, Any]):
    # Insere uma linha JSON na tabela especificada.
    table_ref = f"{PROJECT_ID}.{DATASET}.{table}"
    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        raise RuntimeError(f"Error inserting into {table}: {errors}")

async def update(table: str, id: str, data: Dict[str, Any]):
    # Atualiza uma linha por id na tabela especificada.
    set_clause = ", ".join([f"{k}=@{k}" for k in data.keys()])
    table_ref = f"`{PROJECT_ID}.{DATASET}.{table}`"
    sql = f""" 
UPDATE {table_ref}
SET {set_clause}
WHERE id=@id
"""
    params = [bigquery.ScalarQueryParameter("id", "STRING", id)]
    for k, v in data.items():
        params.append(bigquery.ScalarQueryParameter(k, "STRING", v))
    client.query(sql, job_config=QueryJobConfig(query_parameters=params)).result()

async def delete(table: str, id: str):
    # Deleta uma linha por id na tabela especificada.
    table_ref = f"`{PROJECT_ID}.{DATASET}.{table}`"
    sql = f"DELETE FROM {table_ref} WHERE id=@id"
    job_config = QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", id)])
    client.query(sql, job_config=job_config).result()

async def query_user(username: str):
    # Busca usuário por username na tabela Users.
    return await query("Users", {"username": username})
