
from pandas.testing import assert_frame_equal

from src.failure_risk.generators.master_data import generate_master_data


def test_master_data_counts():
    data = generate_master_data(
        plants_count=1,
        lines_count=2,
        machines_count=10,
        sensors_count=50,
    )

    assert len(data["plants"]) == 1
    assert len(data["production_lines"]) == 2
    assert len(data["machines"]) == 10
    assert len(data["sensors"]) == 50


def test_master_data_foreign_keys():
    data = generate_master_data()

    assert set(data["production_lines"]["plant_id"]).issubset(
        set(data["plants"]["plant_id"])
    )

    assert set(data["machines"]["line_id"]).issubset(
        set(data["production_lines"]["line_id"])
    )

    assert set(data["sensors"]["machine_id"]).issubset(
        set(data["machines"]["machine_id"])
    )


def test_master_data_ids_are_unique():
    data = generate_master_data()

    for frame, key in [
        (data["plants"], "plant_id"),
        (data["production_lines"], "line_id"),
        (data["machines"], "machine_id"),
        (data["sensors"], "sensor_id"),
    ]:
        assert frame[key].is_unique


def test_master_data_is_reproducible():
    first = generate_master_data(seed=20261022)
    second = generate_master_data(seed=20261022)

    for entity in first:
        assert_frame_equal(first[entity], second[entity])

def test_full_hierarchy_counts():
    data = generate_master_data(
        plants_count=3,
        lines_count=12,
        machines_count=100,
        sensors_count=500,
        seed=20261022,
    )

    assert len(data["plants"]) == 3
    assert len(data["production_lines"]) == 12
    assert len(data["machines"]) == 100
    assert len(data["sensors"]) == 500

    # Every plant has at least one line.
    assert (
        data["production_lines"]
        .groupby("plant_id")
        .size()
        .min()
        >= 1
    )

    # Every line has at least one machine.
    assert (
        data["machines"]
        .groupby("line_id")
        .size()
        .min()
        >= 1
    )

    # Every machine has at least one sensor.
    assert (
        data["sensors"]
        .groupby("machine_id")
        .size()
        .min()
        >= 1
    )
