
from __future__ import annotations

import random
from typing import Any

import pandas as pd


SENSOR_TYPES = {
    "TEMP": {
        "unit": "degC",
        "min_value": 0,
        "max_value": 150,
    },
    "VIBRATION": {
        "unit": "mm/s",
        "min_value": 0,
        "max_value": 50,
    },
    "PRESSURE": {
        "unit": "kPa",
        "min_value": 0,
        "max_value": 1500,
    },
    "CURRENT": {
        "unit": "A",
        "min_value": 0,
        "max_value": 500,
    },
}


def generate_master_data(
    plants_count: int = 1,
    lines_count: int = 2,
    machines_count: int = 10,
    sensors_count: int = 50,
    seed: int = 20261022,
) -> dict[str, pd.DataFrame]:
    """Generate deterministic master data with valid parent IDs.

    lines_count is the TOTAL number of production lines across all plants.
    """

    counts = {
        "plants": plants_count,
        "lines": lines_count,
        "machines": machines_count,
        "sensors": sensors_count,
    }

    if any(count < 1 for count in counts.values()):
        raise ValueError("All entity counts must be at least 1.")

    if lines_count < plants_count:
        raise ValueError("Every plant must have at least one line.")

    if machines_count < lines_count:
        raise ValueError("Every line must have at least one machine.")

    if sensors_count < machines_count:
        raise ValueError("Every machine must have at least one sensor.")

    rng = random.Random(seed)

    # 1. Plants
    plants: list[dict[str, Any]] = []

    for p in range(1, plants_count + 1):
        plants.append({
            "plant_id": f"PLT-{p:03d}",
            "plant_name": f"Manufacturing Plant {p:03d}",
            "location": f"Industrial Zone {p:03d}",
            "status": "ACTIVE",
        })

    # 2. Production lines: distribute the total across plants.
    plant_ids = [p["plant_id"] for p in plants]
    lines: list[dict[str, Any]] = []

    for index in range(1, lines_count + 1):
        plant_id = plant_ids[(index - 1) % plants_count]
        local_number = (
            1
            + sum(
                1 for line in lines
                if line["plant_id"] == plant_id
            )
        )

        lines.append({
            "line_id": f"LINE-{plant_id}-{local_number:03d}",
            "plant_id": plant_id,
            "line_name": f"Production Line {local_number:03d}",
            "status": "ACTIVE",
        })

    # 3. Machines
    machines: list[dict[str, Any]] = []
    line_ids = [line["line_id"] for line in lines]

    for index in range(1, machines_count + 1):
        line_id = line_ids[(index - 1) % lines_count]
        machine_id = f"MCH-{line_id}-{index:03d}"

        machines.append({
            "machine_id": machine_id,
            "line_id": line_id,
            "machine_name": f"Machine {index:03d}",
            "machine_type": rng.choice([
                "MOTOR",
                "PUMP",
                "CONVEYOR",
                "COMPRESSOR",
            ]),
            "operating_state": "RUNNING",
            "installation_date": "2022-01-01",
            "status": "ACTIVE",
        })

    # 4. Sensors
    sensors: list[dict[str, Any]] = []
    sensor_type_names = list(SENSOR_TYPES)
    per_machine_type_counter: dict[tuple[str, str], int] = {}

    machine_ids = [machine["machine_id"] for machine in machines]

    for index in range(sensors_count):
        machine_id = machine_ids[index % machines_count]
        sensor_type = sensor_type_names[index % len(sensor_type_names)]

        key = (machine_id, sensor_type)
        per_machine_type_counter[key] = (
            per_machine_type_counter.get(key, 0) + 1
        )
        sensor_number = per_machine_type_counter[key]

        sensor_id = (
            f"SNS-{machine_id}-{sensor_type}-{sensor_number:02d}"
        )
        spec = SENSOR_TYPES[sensor_type]

        sensors.append({
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "sensor_type": sensor_type,
            "unit": spec["unit"],
            "min_value": spec["min_value"],
            "max_value": spec["max_value"],
            "status": "ACTIVE",
        })

    result = {
        "plants": pd.DataFrame(plants),
        "production_lines": pd.DataFrame(lines),
        "machines": pd.DataFrame(machines),
        "sensors": pd.DataFrame(sensors),
    }

    validate_master_data(result)

    return result


def validate_master_data(
    data: dict[str, pd.DataFrame],
) -> None:
    """Raise ValueError when master data violates key constraints."""

    primary_keys = {
        "plants": "plant_id",
        "production_lines": "line_id",
        "machines": "machine_id",
        "sensors": "sensor_id",
    }

    for table, key in primary_keys.items():
        if data[table][key].isna().any():
            raise ValueError(f"{table}.{key} contains null IDs.")

        if not data[table][key].is_unique:
            raise ValueError(f"{table}.{key} contains duplicate IDs.")

    relationships = [
        ("production_lines", "plant_id", "plants", "plant_id"),
        ("machines", "line_id", "production_lines", "line_id"),
        ("sensors", "machine_id", "machines", "machine_id"),
    ]

    for child, child_key, parent, parent_key in relationships:
        valid_parent_ids = set(data[parent][parent_key])
        child_ids = set(data[child][child_key])

        missing = child_ids - valid_parent_ids

        if missing:
            raise ValueError(
                f"{child}.{child_key} references unknown "
                f"{parent}.{parent_key}: {sorted(missing)[:5]}"
            )

    for sensor in data["sensors"].to_dict("records"):
        spec = SENSOR_TYPES.get(sensor["sensor_type"])

        if spec is None:
            raise ValueError(
                f"Unsupported sensor type: {sensor['sensor_type']}"
            )

        if sensor["unit"] != spec["unit"]:
            raise ValueError(
                f"Incorrect unit for sensor {sensor['sensor_id']}"
            )

        if (
            sensor["min_value"] != spec["min_value"]
            or sensor["max_value"] != spec["max_value"]
        ):
            raise ValueError(
                f"Incorrect range for sensor {sensor['sensor_id']}"
            )
