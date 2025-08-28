"""Utilities for importing CSV files into BigQuery tables."""

from __future__ import annotations

from google.cloud import bigquery

from app.db.bq_client import get_client, get_settings, _format_table


def load_csv_to_table(csv_path: str, table: str, *, skip_leading_rows: int = 1) -> None:
    """Load a CSV file into a BigQuery table truncating existing data.

    Args:
        csv_path: Path to the local CSV file.
        table: Name of the destination table in BigQuery.
        skip_leading_rows: Number of initial rows to skip (e.g. header row).
    """

    client = get_client()
    settings = get_settings()
    table_ref = _format_table(settings, table, quoted=False)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=skip_leading_rows,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(csv_path, "rb") as csv_file:
        job = client.load_table_from_file(csv_file, table_ref, job_config=job_config)
        job.result()
