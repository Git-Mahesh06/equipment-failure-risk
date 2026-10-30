
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from failure_risk.validation import validate_dataset


def create_validation_report(
    data: dict[str, pd.DataFrame],
    output_path: str = "data/reports/validation_report.json",
) -> dict:
    """Validate structured data and write a machine-readable JSON report."""

    errors = validate_dataset(data)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "tables_checked": sorted(data.keys()),
        "table_row_counts": {
            name: len(dataframe)
            for name, dataframe in sorted(data.items())
        },
        "error_count": len(errors),
        "errors": errors,
    }

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return report
