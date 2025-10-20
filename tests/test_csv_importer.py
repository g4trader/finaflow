import os
import sys
import types
import logging
from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

# Ensure the backend directory is on the Python path so ``app`` can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.csv_importer import load_csv_to_table  # noqa: E402


def test_load_csv_to_table(monkeypatch, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id\n1\n")

    recorded: dict[str, object] = {}

    class DummyClient:
        def load_table_from_file(self, file_obj, table, job_config):  # pragma: no cover - call path
            recorded["file_name"] = file_obj.name
            recorded["table"] = table
            recorded["job_config"] = job_config

            class DummyJob:
                def result(self_inner):
                    return None

            return DummyJob()

    def fake_get_client():
        return DummyClient()

    def fake_get_settings():
        return types.SimpleNamespace(PROJECT_ID="p", DATASET="d")

    def fake_format_table(settings, table_name, quoted=False):
        recorded["quoted"] = quoted
        return f"{settings.PROJECT_ID}.{settings.DATASET}.{table_name}"

    monkeypatch.setattr("app.services.csv_importer.get_client", fake_get_client)
    monkeypatch.setattr("app.services.csv_importer.get_settings", fake_get_settings)
    monkeypatch.setattr("app.services.csv_importer._format_table", fake_format_table)

    load_csv_to_table(str(csv_file), "Transactions", skip_leading_rows=2)

    assert recorded["file_name"] == str(csv_file)
    assert recorded["table"] == "p.d.Transactions"
    job_config = recorded["job_config"]
    assert job_config.source_format == bigquery.SourceFormat.CSV
    assert job_config.write_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE
    assert job_config.skip_leading_rows == 2
    assert recorded["quoted"] is False


def test_load_csv_to_table_googleclouderror(monkeypatch, tmp_path, caplog):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id\n1\n")

    class DummyClient:
        def load_table_from_file(self, file_obj, table, job_config):
            raise GoogleCloudError("boom")

    def fake_get_client():
        return DummyClient()

    def fake_get_settings():
        return types.SimpleNamespace(PROJECT_ID="p", DATASET="d")

    def fake_format_table(settings, table_name, quoted=False):
        return f"{settings.PROJECT_ID}.{settings.DATASET}.{table_name}"

    monkeypatch.setattr("app.services.csv_importer.get_client", fake_get_client)
    monkeypatch.setattr("app.services.csv_importer.get_settings", fake_get_settings)
    monkeypatch.setattr("app.services.csv_importer._format_table", fake_format_table)

    with caplog.at_level(logging.ERROR):
        msg = load_csv_to_table(str(csv_file), "Transactions")

    assert "Failed to load CSV to table Transactions" in caplog.text
    assert "Failed to load CSV to table Transactions" in msg


def test_load_csv_to_table_file_not_found(monkeypatch, caplog):
    class DummyClient:
        def load_table_from_file(self, file_obj, table, job_config):  # pragma: no cover - should not call
            raise AssertionError("load_table_from_file should not be called")

    def fake_get_client():
        return DummyClient()

    def fake_get_settings():
        return types.SimpleNamespace(PROJECT_ID="p", DATASET="d")

    def fake_format_table(settings, table_name, quoted=False):
        return f"{settings.PROJECT_ID}.{settings.DATASET}.{table_name}"

    monkeypatch.setattr("app.services.csv_importer.get_client", fake_get_client)
    monkeypatch.setattr("app.services.csv_importer.get_settings", fake_get_settings)
    monkeypatch.setattr("app.services.csv_importer._format_table", fake_format_table)

    with caplog.at_level(logging.ERROR):
        msg = load_csv_to_table("missing.csv", "Transactions")

    assert "CSV file missing.csv not found" in caplog.text
    assert "CSV file missing.csv not found" in msg
