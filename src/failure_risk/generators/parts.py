
import numpy as np
import pandas as pd


PART_CATALOG = [
    {
        "part_name": "Industrial Bearing",
        "part_category": "MECHANICAL",
        "unit_cost": 1250.00,
    },
    {
        "part_name": "Electric Motor",
        "part_category": "ELECTRICAL",
        "unit_cost": 18500.00,
    },
    {
        "part_name": "Drive Belt",
        "part_category": "MECHANICAL",
        "unit_cost": 450.00,
    },
    {
        "part_name": "Air Filter",
        "part_category": "CONSUMABLE",
        "unit_cost": 280.00,
    },
    {
        "part_name": "Pressure Sensor",
        "part_category": "INSTRUMENTATION",
        "unit_cost": 3200.00,
    },
    {
        "part_name": "Cooling Fan",
        "part_category": "ELECTRICAL",
        "unit_cost": 2100.00,
    },
    {
        "part_name": "Hydraulic Seal",
        "part_category": "MECHANICAL",
        "unit_cost": 175.00,
    },
    {
        "part_name": "Temperature Sensor",
        "part_category": "INSTRUMENTATION",
        "unit_cost": 2700.00,
    },
    {
        "part_name": "Power Contactor",
        "part_category": "ELECTRICAL",
        "unit_cost": 1600.00,
    },
    {
        "part_name": "Lubricant Cartridge",
        "part_category": "CONSUMABLE",
        "unit_cost": 350.00,
    },
]


def generate_parts(
    parts_count: int = 50,
    seed: int = 20261022,
) -> pd.DataFrame:
    """Generate a reproducible synthetic spare-parts inventory."""

    if isinstance(parts_count, bool) or not isinstance(parts_count, int):
        raise ValueError("parts_count must be an integer")

    if parts_count <= 0:
        raise ValueError("parts_count must be greater than zero")

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")

    rng = np.random.default_rng(seed)
    records = []

    for index in range(parts_count):
        catalog_index = int(rng.integers(0, len(PART_CATALOG)))
        catalog_item = PART_CATALOG[catalog_index]

        stock_quantity = int(rng.integers(0, 101))
        reorder_level = int(rng.integers(10, 31))

        records.append(
            {
                "part_id": f"PART-{index + 1:05d}",
                "part_name": catalog_item["part_name"],
                "part_category": catalog_item["part_category"],
                "unit_cost": catalog_item["unit_cost"],
                "stock_quantity": stock_quantity,
                "reorder_level": reorder_level,
                "supplier_id": f"SUP-{catalog_index + 1:03d}",
                "requires_reorder": stock_quantity <= reorder_level,
            }
        )

    return pd.DataFrame(records)
