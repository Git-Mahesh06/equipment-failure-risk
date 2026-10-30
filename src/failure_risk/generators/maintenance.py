
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


MAINTENANCE_TYPES = [
    "PREVENTIVE",
    "CORRECTIVE",
    "INSPECTION",
    "PREDICTIVE",
]

MAINTENANCE_STATUSES = [
    "COMPLETED",
    "IN_PROGRESS",
    "SCHEDULED",
]

PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]


def generate_maintenance_work_orders(
    machines: pd.DataFrame,
    work_orders_count: int = 250,
    technicians_count: int = 20,
    start_time: str = "2026-01-01T00:00:00",
    days: int = 90,
    seed: int = 20261022,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate reproducible synthetic maintenance work orders and technicians."""

    if machines.empty:
        raise ValueError("machines must not be empty")

    if "machine_id" not in machines.columns:
        raise ValueError("machines must contain a machine_id column")

    if machines["machine_id"].isna().any():
        raise ValueError("machine_id values must not be null")

    if machines["machine_id"].duplicated().any():
        raise ValueError("machine_id values must be unique")

    if work_orders_count < 1:
        raise ValueError("work_orders_count must be at least 1")

    if technicians_count < 1:
        raise ValueError("technicians_count must be at least 1")

    if days < 1:
        raise ValueError("days must be at least 1")

    start = pd.Timestamp(start_time)
    end = start + pd.Timedelta(days=days)
    rng = np.random.default_rng(seed)

    technicians = pd.DataFrame(
        [
            {
                "technician_id": f"TECH-{i + 1:04d}",
                "technician_name": f"Technician {i + 1:02d}",
                "specialization": str(
                    rng.choice(
                        [
                            "MECHANICAL",
                            "ELECTRICAL",
                            "INSTRUMENTATION",
                        ]
                    )
                ),
            }
            for i in range(technicians_count)
        ]
    )

    machine_ids = machines["machine_id"].astype(str).to_numpy()
    technician_ids = technicians["technician_id"].to_numpy()
    records: list[dict[str, Any]] = []

    for i in range(work_orders_count):
        start_offset = int(rng.integers(0, days * 24 * 60))
        maintenance_start = start + pd.Timedelta(minutes=start_offset)

        duration_minutes = int(rng.integers(30, 481))
        maintenance_end = maintenance_start + pd.Timedelta(
            minutes=duration_minutes
        )

        # Do not allow maintenance to extend beyond the observation window.
        maintenance_end = min(maintenance_end, end)

        status = str(rng.choice(MAINTENANCE_STATUSES))
        actual_end = (
            maintenance_end
            if status == "COMPLETED"
            else pd.NaT
        )

        records.append(
            {
                "work_order_id": f"WO-{i + 1:05d}",
                "machine_id": str(rng.choice(machine_ids)),
                "technician_id": str(rng.choice(technician_ids)),
                "maintenance_type": str(rng.choice(MAINTENANCE_TYPES)),
                "priority": str(rng.choice(PRIORITIES)),
                "status": status,
                "planned_start": maintenance_start,
                "planned_end": maintenance_end,
                "actual_start": (
                    maintenance_start
                    if status in {"COMPLETED", "IN_PROGRESS"}
                    else pd.NaT
                ),
                "actual_end": actual_end,
                "duration_minutes": duration_minutes,
            }
        )

    work_orders = pd.DataFrame(records)

    return work_orders, technicians
