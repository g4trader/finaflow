import os
import subprocess
from pathlib import Path


def test_cli_calls_load_csv_for_each_path(tmp_path):
    calls_file = tmp_path / "calls.txt"
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text(
        "import os\n"
        "from app.services import csv_importer\n"
        "def fake_load_csv_to_table(path, table, skip_leading_rows=1):\n"
        "    with open(os.environ['CALLS_FILE'], 'a', encoding='utf-8') as f:\n"
        "        f.write(f'{path}|{table}|{skip_leading_rows}\\n')\n"
        "csv_importer.load_csv_to_table = fake_load_csv_to_table\n",
        encoding="utf-8",
    )

    csv1 = tmp_path / "first.csv"
    csv1.write_text("id\n1\n", encoding="utf-8")
    csv2 = tmp_path / "second.csv"
    csv2.write_text("id\n2\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["CALLS_FILE"] = str(calls_file)

    backend_dir = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            "python",
            "import_csv.py",
            str(csv1),
            str(csv2),
            "-t",
            "PlanOfAccounts",
        ],
        cwd=backend_dir,
        check=True,
        env=env,
    )

    recorded = calls_file.read_text(encoding="utf-8").strip().splitlines()
    assert recorded == [
        f"{csv1}|PlanOfAccounts|1",
        f"{csv2}|PlanOfAccounts|1",
    ]

