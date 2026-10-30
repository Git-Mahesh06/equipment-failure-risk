from __future__ import annotations

from pathlib import Path

import pandas as pd

from failure_risk.validation import validate_dataset

from failure_risk.generators.master_data import generate_master_data
from failure_risk.generators.failure_events import generate_failure_events
from failure_risk.generators.telemetry import write_telemetry_csv
from failure_risk.generators.maintenance import (
    generate_maintenance_work_orders,
)
from failure_risk.generators.operating_shifts import (
    generate_operating_shifts,
)
from failure_risk.generators.parts import generate_parts
from failure_risk.generators.parts_usage import generate_parts_usage


def generate_dataset(
    plants_count: int = 3,
    lines_count: int = 12,
    machines_count: int = 100,
    sensors_count: int = 500,
    failures_count: int = 150,
    work_orders_count: int = 250,
    technicians_count: int = 20,
    parts_count: int = 50,
    parts_usage_count: int = 300,
    start_time: str = "2026-01-01T00:00:00",
    days: int = 90,
    seed: int = 20261022,
) -> dict[str, pd.DataFrame]:
    """Generate all structured datasets with reproducible settings."""

    data = generate_master_data(
        plants_count=plants_count,
        lines_count=lines_count,
        machines_count=machines_count,
        sensors_count=sensors_count,
        seed=seed,
    )

    data["failure_events"] = generate_failure_events(
        machines=data["machines"],
        failures_count=failures_count,
        start_time=start_time,
        days=days,
        seed=seed,
    )

    work_orders, technicians = generate_maintenance_work_orders(
        machines=data["machines"],
        work_orders_count=work_orders_count,
        technicians_count=technicians_count,
        start_time=start_time,
        days=days,
        seed=seed,
    )
    data["maintenance_work_orders"] = work_orders
    data["technicians"] = technicians

    data["operating_shifts"] = generate_operating_shifts(
        machines=data["machines"],
        start_time=start_time,
        days=days,
    )

    data["parts"] = generate_parts(
        parts_count=parts_count,
        seed=seed,
    )

    data["parts_usage"] = generate_parts_usage(
        work_orders=data["maintenance_work_orders"],
        parts=data["parts"],
        usage_count=parts_usage_count,
        seed=seed,
    )

    return data


def write_dataset_telemetry(
    data: dict[str, pd.DataFrame],
    output_path: str = "data/raw/telemetry.csv",
    start_time: str = "2026-01-01T00:00:00",
    days: int = 90,
    interval_minutes: int = 30,
    seed: int = 20261022,
    precursor_hours: int = 24,
) -> int:
    """Stream telemetry linked to the earliest failure per machine."""

    failures = data["failure_events"]


    earliest_failures = (
        failures.sort_values("failure_timestamp")
        .drop_duplicates(subset=["machine_id"], keep="first")
    )

    failure_schedule = {
        row["machine_id"]: {
            "timestamp": row["failure_timestamp"],
            "failure_type": row["failure_type"],
        }
        for _, row in earliest_failures.iterrows()
    }


    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    return write_telemetry_csv(
        sensors=data["sensors"],
        machines=data["machines"],
        output_path=output_path,
        start_time=start_time,
        days=days,
        interval_minutes=interval_minutes,
        seed=seed,
        failure_schedule=failure_schedule,
        precursor_hours=precursor_hours,
    )


def export_dataset(
    data: dict[str, pd.DataFrame],
    output_dir: str = "data/raw",
    ground_truth_dir: str = "data/ground_truth",
) -> dict[str, str]:
    """Validate structured datasets before exporting CSV files."""

    errors = validate_dataset(data)

    if errors:
        error_details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(
            f"Dataset validation failed; no files were exported:\n{error_details}"
        )

    raw_path = Path(output_dir)
    truth_path = Path(ground_truth_dir)

    raw_path.mkdir(parents=True, exist_ok=True)
    truth_path.mkdir(parents=True, exist_ok=True)

    exported_files: dict[str, str] = {}

    for name, dataframe in data.items():
        if name == "failure_events":
            destination = truth_path / "failure_events.csv"
        else:
            destination = raw_path / f"{name}.csv"

        dataframe.to_csv(destination, index=False)
        exported_files[name] = str(destination)

    return exported_files
