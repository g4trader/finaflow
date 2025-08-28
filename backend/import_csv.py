"""CLI utility to import CSV files into BigQuery tables."""

from __future__ import annotations

import argparse

from app.services.csv_importer import load_csv_to_table

TABLE_CHOICES = ["PlanOfAccounts", "Transactions", "Forecasts"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import CSV files into BigQuery tables"
    )
    parser.add_argument(
        "csv_paths", nargs="+", help="Path(s) to CSV file(s) to import"
    )
    parser.add_argument(
        "--table", "-t", required=True, choices=TABLE_CHOICES,
        help="Destination table name"
    )
    parser.add_argument(
        "--skip-leading-rows", type=int, default=1,
        help="Number of initial rows to skip (default: 1)"
    )

    args = parser.parse_args()

    for path in args.csv_paths:
        load_csv_to_table(path, args.table, skip_leading_rows=args.skip_leading_rows)


if __name__ == "__main__":
    main()
