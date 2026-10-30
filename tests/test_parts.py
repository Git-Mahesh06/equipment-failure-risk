
import pandas as pd
import pytest

from failure_risk.generators.parts import generate_parts


def test_generates_requested_number_of_parts():
    parts = generate_parts(parts_count=50)

    assert len(parts) == 50


def test_part_ids_are_unique():
    parts = generate_parts(parts_count=100)

    assert parts["part_id"].is_unique


def test_part_inventory_values_are_valid():
    parts = generate_parts()

    assert (parts["unit_cost"] > 0).all()
    assert (parts["stock_quantity"] >= 0).all()
    assert (parts["reorder_level"] > 0).all()


def test_categories_are_from_catalog():
    parts = generate_parts()

    allowed = {
        "MECHANICAL",
        "ELECTRICAL",
        "CONSUMABLE",
        "INSTRUMENTATION",
    }

    assert set(parts["part_category"]).issubset(allowed)


def test_reorder_flag_is_correct():
    parts = generate_parts()

    expected = parts["stock_quantity"] <= parts["reorder_level"]

    assert (parts["requires_reorder"] == expected).all()


def test_generation_is_reproducible():
    first = generate_parts(parts_count=30, seed=123)
    second = generate_parts(parts_count=30, seed=123)

    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_can_produce_different_inventory():
    first = generate_parts(parts_count=50, seed=1)
    second = generate_parts(parts_count=50, seed=2)

    assert not first.equals(second)


@pytest.mark.parametrize("invalid_count", [0, -1, -10])
def test_rejects_nonpositive_part_counts(invalid_count):
    with pytest.raises(ValueError, match="greater than zero"):
        generate_parts(parts_count=invalid_count)


@pytest.mark.parametrize("invalid_count", [1.5, "50", None, True])
def test_rejects_noninteger_part_counts(invalid_count):
    with pytest.raises(ValueError, match="must be an integer"):
        generate_parts(parts_count=invalid_count)


def test_rejects_noninteger_seed():
    with pytest.raises(ValueError, match="seed must be an integer"):
        generate_parts(seed="fixed")
