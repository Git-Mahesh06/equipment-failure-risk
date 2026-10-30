
from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime

import numpy as np
import pandas as pd


SENSOR_PROFILES = {
    "TEMP": {
        "unit": "degC",
        "minimum": 0.0,
        "maximum": 150.0,
        "baseline": 65.0,
        "noise": 2.0,
        "drift": 18.0,
    },
    "VIBRATION": {
        "unit": "mm/s",
        "minimum": 0.0,
        "maximum": 50.0,
        "baseline": 3.0,
        "noise": 0.5,
        "drift": 8.0,
    },
    "PRESSURE": {
        "unit": "kPa",
        "minimum": 0.0,
        "maximum": 1500.0,
        "baseline": 600.0,
        "noise": 15.0,
        "drift": 100.0,
    },
    "CURRENT": {
        "unit": "A",
        "minimum": 0.0,
        "maximum": 500.0,
        "baseline": 50.0,
        "noise": 3.0,
        "drift": 12.0,
    },
}


def iter_telemetry_chunks(
    sensors: pd.DataFrame,
    machines: pd.DataFrame,
    start_time: str | datetime = "2026-01-01T00:00:00",
    days: int = 90,
    interval_minutes: int = 30,
    seed: int = 20261022,
    failure_schedule: Mapping[str, str | datetime] | None = None,
    precursor_hours: int = 24,
) -> Iterator[pd.DataFrame]:
    """Yield deterministic telemetry in one-sensor chunks.

    failure_schedule maps machine IDs to their simulated failure times.
    Only telemetry before a failure receives its simulated precursor trend.

    Ground-truth labels are intentionally not included in telemetry.
    """

    if days < 1 or interval_minutes < 1:
        raise ValueError("days and interval_minutes must be positive.")

    if 1440 % interval_minutes != 0:
        raise ValueError(
            "interval_minutes must divide evenly into 1440 minutes."
        )

    if precursor_hours < 0:
        raise ValueError("precursor_hours cannot be negative.")

    required_sensor_columns = {
        "sensor_id", "machine_id", "sensor_type", "unit"
    }
    required_machine_columns = {"machine_id"}

    if not required_sensor_columns.issubset(sensors.columns):
        raise ValueError("Sensors DataFrame is missing required columns.")

    if not required_machine_columns.issubset(machines.columns):
        raise ValueError("Machines DataFrame is missing machine_id.")

    if sensors["sensor_id"].isna().any() or not sensors["sensor_id"].is_unique:
        raise ValueError("Sensor IDs must be non-null and unique.")

    if machines["machine_id"].isna().any() or not machines["machine_id"].is_unique:
        raise ValueError("Machine IDs must be non-null and unique.")

    valid_machine_ids = set(machines["machine_id"])
    referenced_machine_ids = set(sensors["machine_id"])

    if not referenced_machine_ids.issubset(valid_machine_ids):
        raise ValueError("A sensor references an unknown machine.")

    if not sensors["sensor_type"].isin(SENSOR_PROFILES).all():
        raise ValueError("Unsupported sensor type found.")

    for sensor in sensors.to_dict("records"):
        expected_unit = SENSOR_PROFILES[sensor["sensor_type"]]["unit"]
        if sensor["unit"] != expected_unit:
            raise ValueError(
                f"Incorrect unit for sensor {sensor['sensor_id']}: "
                f"expected {expected_unit}, got {sensor['unit']}."
            )

    start = pd.Timestamp(start_time)
    if start.tz is not None:
        raise ValueError("Use timezone-naive timestamps consistently.")

    total_readings_per_sensor = (
        days * 24 * 60 // interval_minutes
    )

    timestamps = pd.date_range(
        start=start,
        periods=total_readings_per_sensor,
        freq=f"{interval_minutes}min",
    )

    failures = {
        machine_id: pd.Timestamp(failure_time)
        for machine_id, failure_time in (failure_schedule or {}).items()
    }

    unknown_failure_machines = set(failures) - valid_machine_ids
    if unknown_failure_machines:
        raise ValueError("Failure schedule references an unknown machine.")

    for sensor_index, sensor in enumerate(
        sensors.sort_values("sensor_id").to_dict("records")
    ):
        sensor_id = sensor["sensor_id"]
        machine_id = sensor["machine_id"]
        sensor_type = sensor["sensor_type"]
        profile = SENSOR_PROFILES[sensor_type]

        # Independent, reproducible random stream for each sensor.
        rng = np.random.default_rng(seed + sensor_index)

        # Simulate normal operation and a daily two-hour shutdown.
        running = ~timestamps.hour.isin([2, 3])

        values = rng.normal(
            loc=profile["baseline"],
            scale=profile["noise"],
            size=total_readings_per_sensor,
        )

        values[~running] = 0.0

        # Simulate a gradual precursor trend before a scheduled failure.
        failure_time = failures.get(machine_id)

        if failure_time is not None and precursor_hours > 0:
            elapsed_to_failure = (
                failure_time - timestamps
            ).total_seconds() / 3600

            precursor_mask = (
                (elapsed_to_failure > 0)
                & (elapsed_to_failure <= precursor_hours)
                & running
            )

            progress = (
                1 - elapsed_to_failure[precursor_mask] / precursor_hours
            )

            values[precursor_mask] += profile["drift"] * progress

        # Clip simulated readings to the instrument's physical limits.
        values = np.clip(
            values,
            profile["minimum"],
            profile["maximum"],
        )

        quality = np.full(
            total_readings_per_sensor,
            "GOOD",
            dtype=object,
        )
        quality[~running] = "SHUTDOWN"

        telemetry_ids = [
            f"TEL-{sensor_id}-{ts.strftime('%Y%m%dT%H%M%S')}"
            for ts in timestamps
        ]

        yield pd.DataFrame({
            "telemetry_id": telemetry_ids,
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "timestamp": timestamps,
            "operating_state": np.where(running, "RUNNING", "STOPPED"),
            "value": values,
            "unit": profile["unit"],
            "quality_status": quality,
        })


def write_telemetry_csv(
    sensors: pd.DataFrame,
    machines: pd.DataFrame,
    output_path: str,
    **generator_kwargs,
) -> int:
    """Stream telemetry chunks to CSV and return the reading count."""

    total_rows = 0
    first_chunk = True

    for chunk in iter_telemetry_chunks(
        sensors=sensors,
        machines=machines,
        **generator_kwargs,
    ):
        chunk.to_csv(
            output_path,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )

        total_rows += len(chunk)
        first_chunk = False

    if first_chunk:
        raise ValueError("No sensors were provided.")

    return total_rows
