
import pandas as pd

from failure_risk.pipeline import generate_dataset
from failure_risk.validation import validate_dataset


def test_generated_dataset_passes_validation():
    data = generate_dataset(days=1, seed=12345)

    errors = validate_dataset(data)

    assert errors == [], f"Validation errors: {errors}"


def test_validator_detects_duplicate_primary_key():
    data = generate_dataset(days=1, seed=12345)

    data["plants"] = pd.concat(
        [data["plants"], data["plants"].iloc[[0]]],
        ignore_index=True,
    )

    errors = validate_dataset(data)

    assert any(
        "plants.plant_id contains duplicate IDs" in error
        for error in errors
    )


def test_validator_detects_invalid_machine_reference():
    data = generate_dataset(days=1, seed=12345)

    data["machines"].loc[0, "line_id"] = "LINE-DOES-NOT-EXIST"

    errors = validate_dataset(data)

    assert any(
        "machines.line_id contains unknown references" in error
        for error in errors
    )


def test_validator_detects_invalid_parts_usage_cost():
    data = generate_dataset(days=1, seed=12345)

    data["parts_usage"].loc[0, "total_cost"] += 100

    errors = validate_dataset(data)

    assert any(
        "Parts usage total_cost does not match" in error
        for error in errors
    )
