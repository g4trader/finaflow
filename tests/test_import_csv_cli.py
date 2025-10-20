import json
import os
import subprocess
from pathlib import Path


def test_cli_invokes_loader_for_each_csv(tmp_path):
    """Run the CLI and ensure each CSV file is passed to load_csv_to_table."""
    calls_file = tmp_path / "calls.json"
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text(
        "import os, json, atexit\n"
        "from unittest.mock import MagicMock\n"
        "from app.services import csv_importer\n"
        "mock = MagicMock()\n"
        "csv_importer.load_csv_to_table = mock\n"
        "def dump():\n"
        "    with open(os.environ['CALLS_FILE'], 'w', encoding='utf-8') as f:\n"
        "        json.dump([{'args': list(c.args), 'kwargs': c.kwargs} for c in mock.call_args_list], f)\n"
        "atexit.register(dump)\n",
        encoding="utf-8",
    )

    csv1 = tmp_path / "first.csv"
    csv1.write_text("id\n1\n", encoding="utf-8")
    csv2 = tmp_path / "second.csv"
    csv2.write_text("id\n2\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["CALLS_FILE"] = str(calls_file)

    subprocess.run(
        [
            "python",
            "import_csv.py",
            str(csv1),
            str(csv2),
            "-t",
            "PlanOfAccounts",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        env=env,
    )

    calls = json.loads(calls_file.read_text(encoding="utf-8"))
    assert calls == [
        {
            "args": [str(csv1), "PlanOfAccounts"],
            "kwargs": {"skip_leading_rows": 1},
        },
        {
            "args": [str(csv2), "PlanOfAccounts"],
            "kwargs": {"skip_leading_rows": 1},
        },
    ]
