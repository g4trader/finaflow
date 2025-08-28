import os
import subprocess
from pathlib import Path


def test_cli_invokes_loader_for_each_csv(tmp_path):
    """Run the CLI and ensure each CSV file is passed to load_csv_to_table."""
    calls_file = tmp_path / "calls.txt"
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text(
        "import os\n"
        "from app.services import csv_importer\n"
        "def fake(path, table, skip_leading_rows=1):\n"
        "    with open(os.environ['CALLS_FILE'], 'a', encoding='utf-8') as f:\n"
        "        f.write(f'{path}|{table}|{skip_leading_rows}\\n')\n"
        "csv_importer.load_csv_to_table = fake\n",
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

    calls = calls_file.read_text(encoding="utf-8").strip().splitlines()
    assert calls == [
        f"{csv1}|PlanOfAccounts|1",
        f"{csv2}|PlanOfAccounts|1",
    ]
