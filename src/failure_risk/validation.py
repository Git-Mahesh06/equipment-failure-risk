
from __future__ import annotations

import pandas as pd


PRIMARY_KEYS = {
    "plants": "plant_id",
    "production_lines": "line_id",
    "machines": "machine_id",
    "sensors": "sensor_id",
    "failure_events": "failure_id",
    "maintenance_work_orders": "work_order_id",
    "technicians": "technician_id",
    "operating_shifts": "shift_id",
    "parts": "part_id",
    "parts_usage": "usage_id",
}

FOREIGN_KEYS = [
    ("production_lines", "plant_id", "plants", "plant_id"),
    ("machines", "line_id", "production_lines", "line_id"),
    ("sensors", "machine_id", "machines", "machine_id"),
    ("failure_events", "machine_id", "machines", "machine_id"),
    ("maintenance_work_orders", "machine_id", "machines", "machine_id"),
    ("maintenance_work_orders", "technician_id", "technicians", "technician_id"),
    ("operating_shifts", "machine_id", "machines", "machine_id"),
    ("parts_usage", "work_order_id", "maintenance_work_orders", "work_order_id"),
    ("parts_usage", "part_id", "parts", "part_id"),
]


def validate_dataset(data: dict[str, pd.DataFrame]) -> list[str]:
    """Return a list of dataset integrity errors; an empty list means valid."""

    errors: list[str] = []

    # Check required tables and primary keys.
    for table, key in PRIMARY_KEYS.items():
        if table not in data:
            errors.append(f"Missing required table: {table}")
            continue

        df = data[table]

        if key not in df.columns:
            errors.append(f"{table} is missing primary-key column {key}")
            continue

        if df[key].isna().any():
            errors.append(f"{table}.{key} contains null values")

        if df[key].duplicated().any():
            errors.append(f"{table}.{key} contains duplicate IDs")

    # Check foreign-key relationships where both tables and columns exist.
    for child, child_key, parent, parent_key in FOREIGN_KEYS:
        if child not in data or parent not in data:
            continue

        child_df = data[child]
        parent_df = data[parent]

        if child_key not in child_df.columns or parent_key not in parent_df.columns:
            errors.append(
                f"Cannot validate {child}.{child_key} -> {parent}.{parent_key}: "
                "a required column is missing"
            )
            continue

        parent_ids = set(parent_df[parent_key].dropna())
        invalid = child_df.loc[
            child_df[child_key].notna()
            & ~child_df[child_key].isin(parent_ids),
            child_key,
        ]

        if not invalid.empty:
            errors.append(
                f"{child}.{child_key} contains unknown references: "
                f"{invalid.astype(str).drop_duplicates().head(5).tolist()}"
            )

    # Validate maintenance time ordering.
    if "maintenance_work_orders" in data:
        df = data["maintenance_work_orders"]
        required = {"planned_start", "planned_end", "actual_start", "actual_end", "status"}

        if required.issubset(df.columns):
            planned_start = pd.to_datetime(df["planned_start"], errors="coerce")
            planned_end = pd.to_datetime(df["planned_end"], errors="coerce")
            actual_start = pd.to_datetime(df["actual_start"], errors="coerce")
            actual_end = pd.to_datetime(df["actual_end"], errors="coerce")

            if (planned_start.isna() | planned_end.isna()).any():
                errors.append("Maintenance planned timestamps contain invalid values")

            if (planned_end < planned_start).any():
                errors.append("Maintenance planned_end occurs before planned_start")

            if (actual_end.notna() & actual_start.isna()).any():
                errors.append("Maintenance actual_end exists without actual_start")

            if (actual_end.notna() & (actual_end < actual_start)).any():
                errors.append("Maintenance actual_end occurs before actual_start")

            completed = df["status"].eq("COMPLETED")

            if (completed & actual_end.isna()).any():
                errors.append("Completed maintenance orders must have actual_end")

    # Parts usage must only reference completed work orders.
    if {"parts_usage", "maintenance_work_orders"}.issubset(data):
        usage = data["parts_usage"]
        orders = data["maintenance_work_orders"]

        if {"work_order_id", "status"}.issubset(orders.columns) and "work_order_id" in usage.columns:
            status_by_order = orders.set_index("work_order_id")["status"]
            referenced_status = usage["work_order_id"].map(status_by_order)

            if referenced_status.isna().any():
                errors.append("Parts usage references unknown work orders")

            if referenced_status.notna().any() and referenced_status.dropna().ne("COMPLETED").any():
                errors.append("Parts usage references non-completed work orders")

    # Validate parts usage arithmetic.
    if "parts_usage" in data:
        usage = data["parts_usage"]

        if {"quantity_used", "unit_cost", "total_cost"}.issubset(usage.columns):
            expected_cost = (usage["quantity_used"] * usage["unit_cost"]).round(2)

            if (usage["quantity_used"].isna() | (usage["quantity_used"] <= 0)).any():
                errors.append("Parts usage quantity_used must be positive")

            if (usage["unit_cost"].isna() | (usage["unit_cost"] <= 0)).any():
                errors.append("Parts usage unit_cost must be positive")

            if not expected_cost.eq(usage["total_cost"].round(2)).all():
                errors.append("Parts usage total_cost does not match quantity_used * unit_cost")

    return errors
