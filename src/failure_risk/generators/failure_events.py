
from __future__ import annotations

from typing import Any

import pandas as pd


FAILURE_TYPES = [
    "OVERHEATING",
    "EXCESSIVE_VIBRATION",
    "PRESSURE_LOSS",
    "ELECTRICAL_FAULT",
    "BEARING_WEAR",
]

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

ROOT_CAUSES = [
    "INSUFFICIENT_LUBRICATION",
    "COMPONENT_WEAR",
    "COOLING_FAILURE",
    "ELECTRICAL_DEGRADATION",
    "OPERATING_STRESS",
]


def generate_failure_events(
    machines: pd.DataFrame,
    failures_count: int = 150,
    start_time: str = "2026-01-01T00:00:00",
    days: int = 90,
    seed: int = 20261022,
) -> pd.DataFrame:
    """Generate deterministic synthetic equipment failure events.

    Each failure is assigned to a valid machine. Repeated failures on the
    same machine are allowed because a machine may fail more than once.
    """

    if machines.empty:
        raise ValueError("machines must not be empty")

    if "machine_id" not in machines.columns:
        raise ValueError("machines must contain a machine_id column")

    if machines["machine_id"].isna().any():
        raise ValueError("machine_id values must not be null")

    if machines["machine_id"].duplicated().any():
        raise ValueError("machine_id values must be unique")

    if not 100 <= failures_count <= 200:
        raise ValueError("failures_count must be between 100 and 200")

    if days <= 0:
        raise ValueError("days must be greater than zero")

    start = pd.Timestamp(start_time)
    end = start + pd.Timedelta(days=days)

    rng = __import__("numpy").random.default_rng(seed)
    machine_ids = machines["machine_id"].to_numpy()

    records: list[dict[str, Any]] = []

    for index in range(failures_count):
        machine_id = str(rng.choice(machine_ids))

        # Generate timestamps within the requested observation window.
        offset_seconds = int(rng.integers(0, days * 24 * 60 * 60))
        failure_timestamp = start + pd.Timedelta(seconds=offset_seconds)

        records.append(
            {
                "failure_id": f"FAIL-{index + 1:05d}",
                "machine_id": machine_id,
                "failure_type": str(rng.choice(FAILURE_TYPES)),
                "failure_timestamp": failure_timestamp,
                "severity": str(rng.choice(SEVERITIES)),
                "root_cause": str(rng.choice(ROOT_CAUSES)),
                "downtime_minutes": int(rng.integers(30, 1441)),
            }
        )

    result = pd.DataFrame(records)

    # Stable ordering makes output predictable for a fixed seed.
    result = result.sort_values(
        ["failure_timestamp", "failure_id"]
    ).reset_index(drop=True)

    return result
