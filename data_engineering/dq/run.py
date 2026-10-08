import argparse
import datetime
import json
from pathlib import Path

import pandas as pd

from data_engineering.dq.checks import run_dq_checks


def main():
    parser = argparse.ArgumentParser(
        description="Run Data Quality checks independently."
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Directory containing raw CSV files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data_engineering/data/reports/dq_report.json",
        help="Path to write the DQ report JSON",
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    # Read files
    ports_path = input_dir / "ports.csv"
    if not ports_path.exists():
        # Fallback to 'ports 2.csv' if standard name isn't there for testing
        ports_path = input_dir / "ports 2.csv"

    shipments_path = input_dir / "shipments.csv"
    if not shipments_path.exists():
        shipments_path = input_dir / "shipments 2.csv"

    events_path = input_dir / "port_events.csv"
    if not events_path.exists():
        events_path = input_dir / "port_events 2.csv"

    ports_df = pd.read_csv(ports_path)
    shipments_df = pd.read_csv(shipments_path)
    events_df = pd.read_csv(events_path)

    results = run_dq_checks(ports_df, shipments_df, events_df)

    # Generate Report
    report = {
        "execution_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "report_version": "1.0",
        "total_rows": {
            "ports": len(ports_df),
            "shipments": len(shipments_df),
            "port_events": len(events_df),
        },
        "findings": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Data Quality checks completed. Report saved to {output_path}")


if __name__ == "__main__":
    main()
