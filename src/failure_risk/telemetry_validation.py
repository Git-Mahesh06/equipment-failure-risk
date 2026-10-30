
from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "telemetry_id",
    "machine_id",
    "sensor_id",
    "timestamp",
    "value",
}


def validate_telemetry(
    telemetry: pd.DataFrame,
    machines: pd.DataFrame | None = None,
    sensors: pd.DataFrame | None = None,
) -> list[dict]:
    """Validate telemetry records and return machine-readable exceptions."""
    exceptions: list[dict] = []

    missing_columns = REQUIRED_COLUMNS - set(telemetry.columns)
    if missing_columns:
        return [
            {
                "exception_type": "MISSING_COLUMNS",
                "severity": "ERROR",
                "message": f"Missing required columns: {sorted(missing_columns)}",
            }
        ]

    if telemetry.empty:
        exceptions.append({
            "exception_type": "EMPTY_TELEMETRY",
            "severity": "ERROR",
            "message": "Telemetry dataset contains no records.",
        })
        return exceptions

    for column in ["telemetry_id", "machine_id", "sensor_id", "timestamp"]:
        missing_mask = telemetry[column].isna()
        for index in telemetry.index[missing_mask]:
            exceptions.append({
                "exception_type": "NULL_REQUIRED_VALUE",
                "severity": "ERROR",
                "row_index": str(index),
                "column": column,
                "message": f"{column} is missing.",
            })

    duplicate_mask = telemetry["telemetry_id"].duplicated(keep=False)
    for index in telemetry.index[duplicate_mask]:
        exceptions.append({
            "exception_type": "DUPLICATE_TELEMETRY_ID",
            "severity": "ERROR",
            "row_index": str(index),
            "message": "Telemetry ID is duplicated.",
        })

    numeric_values = pd.to_numeric(telemetry["value"], errors="coerce")
    invalid_numeric = numeric_values.isna()
    for index in telemetry.index[invalid_numeric]:
        exceptions.append({
            "exception_type": "INVALID_READING",
            "severity": "ERROR",
            "row_index": str(index),
            "message": "Telemetry reading is not numeric.",
        })

    invalid_timestamp = pd.to_datetime(
        telemetry["timestamp"], errors="coerce"
    ).isna()
    for index in telemetry.index[invalid_timestamp]:
        exceptions.append({
            "exception_type": "INVALID_TIMESTAMP",
            "severity": "ERROR",
            "row_index": str(index),
            "message": "Telemetry timestamp is invalid.",
        })

    if machines is not None and "machine_id" in machines.columns:
        known_machines = set(machines["machine_id"].dropna())
        invalid_machines = ~telemetry["machine_id"].isin(known_machines)
        for index in telemetry.index[invalid_machines]:
            exceptions.append({
                "exception_type": "UNKNOWN_MACHINE",
                "severity": "ERROR",
                "row_index": str(index),
                "message": "Telemetry references an unknown machine.",
            })

    if sensors is not None and {
        "sensor_id", "machine_id"
    }.issubset(sensors.columns):
        sensor_lookup = sensors.set_index("sensor_id")["machine_id"]
        known_sensor_ids = set(sensor_lookup.index)
        unknown_sensors = ~telemetry["sensor_id"].isin(known_sensor_ids)

        for index in telemetry.index[unknown_sensors]:
            exceptions.append({
                "exception_type": "UNKNOWN_SENSOR",
                "severity": "ERROR",
                "row_index": str(index),
                "message": "Telemetry references an unknown sensor.",
            })

        valid_sensor_rows = telemetry[
            telemetry["sensor_id"].isin(known_sensor_ids)
        ]
        expected_machines = valid_sensor_rows["sensor_id"].map(sensor_lookup)
        mismatched = (
            expected_machines.notna()
            & (expected_machines != valid_sensor_rows["machine_id"])
        )

        for index in valid_sensor_rows.index[mismatched]:
            exceptions.append({
                "exception_type": "SENSOR_MACHINE_MISMATCH",
                "severity": "ERROR",
                "row_index": str(index),
                "message": "Sensor does not belong to the referenced machine.",
            })

    return exceptions


def write_exception_report(
    exceptions: list[dict],
    output_path: str | Path = "data/exceptions/telemetry_exceptions.csv",
) -> Path:
    """Write validation exceptions to CSV, including an empty report if clean."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "exception_type",
        "severity",
        "row_index",
        "column",
        "message",
    ]
    pd.DataFrame(exceptions, columns=columns).to_csv(
        destination, index=False
    )
    return destination
