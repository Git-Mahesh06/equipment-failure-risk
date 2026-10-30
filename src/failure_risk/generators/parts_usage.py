
import numpy as np
import pandas as pd


def generate_parts_usage(
    work_orders: pd.DataFrame,
    parts: pd.DataFrame,
    usage_count: int = 300,
    seed: int = 20261022,
) -> pd.DataFrame:
    """
    Generate synthetic spare-parts consumption records for completed
    maintenance work orders.

    Each usage record references an existing work order and part.
    Inventory balances are not modified by this function.
    """

    if not isinstance(usage_count, int) or isinstance(usage_count, bool):
        raise ValueError("usage_count must be an integer")

    if usage_count < 0:
        raise ValueError("usage_count must be zero or greater")

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    if work_orders.empty:
        raise ValueError("work_orders must not be empty")

    if parts.empty:
        raise ValueError("parts must not be empty")

    required_work_order_columns = {"work_order_id", "status"}
    required_part_columns = {"part_id", "unit_cost"}

    if not required_work_order_columns.issubset(work_orders.columns):
        raise ValueError(
            "work_orders must contain work_order_id and status columns"
        )

    if not required_part_columns.issubset(parts.columns):
        raise ValueError("parts must contain part_id and unit_cost columns")

    if work_orders["work_order_id"].isna().any():
        raise ValueError("work_order_id must not contain null values")

    if work_orders["work_order_id"].duplicated().any():
        raise ValueError("work_order_id values must be unique")

    if parts["part_id"].isna().any():
        raise ValueError("part_id must not contain null values")

    if parts["part_id"].duplicated().any():
        raise ValueError("part_id values must be unique")

    if parts["unit_cost"].isna().any() or (parts["unit_cost"] <= 0).any():
        raise ValueError("unit_cost must contain positive values")

    eligible_orders = work_orders[
        work_orders["status"].eq("COMPLETED")
    ].reset_index(drop=True)

    if usage_count > 0 and eligible_orders.empty:
        raise ValueError(
            "at least one COMPLETED work order is required for usage records"
        )

    rng = np.random.default_rng(seed)
    records = []

    for index in range(usage_count):
        order_index = int(rng.integers(0, len(eligible_orders)))
        part_index = int(rng.integers(0, len(parts)))

        order = eligible_orders.iloc[order_index]
        part = parts.iloc[part_index]

        quantity_used = int(rng.integers(1, 6))
        unit_cost = float(part["unit_cost"])

        records.append(
            {
                "usage_id": f"USAGE-{index + 1:06d}",
                "work_order_id": order["work_order_id"],
                "part_id": part["part_id"],
                "quantity_used": quantity_used,
                "unit_cost": unit_cost,
                "total_cost": round(quantity_used * unit_cost, 2),
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "usage_id",
            "work_order_id",
            "part_id",
            "quantity_used",
            "unit_cost",
            "total_cost",
        ],
    )
