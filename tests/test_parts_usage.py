
import pandas as pd
import pytest

from failure_risk.generators.parts_usage import generate_parts_usage


@pytest.fixture
def work_orders():
    return pd.DataFrame(
        {
            "work_order_id": ["WO-001", "WO-002", "WO-003"],
            "status": ["COMPLETED", "SCHEDULED", "COMPLETED"],
        }
    )


@pytest.fixture
def parts():
    return pd.DataFrame(
        {
            "part_id": ["PART-001", "PART-002"],
            "unit_cost": [100.0, 250.0],
        }
    )


def test_generates_requested_number_of_records(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=25)

    assert len(usage) == 25


def test_usage_ids_are_unique(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=50)

    assert usage["usage_id"].is_unique


def test_references_valid_work_orders_and_parts(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=50)

    assert set(usage["work_order_id"]).issubset(
        set(work_orders["work_order_id"])
    )
    assert set(usage["part_id"]).issubset(set(parts["part_id"]))


def test_only_completed_work_orders_are_used(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=100)

    completed_ids = set(
        work_orders.loc[
            work_orders["status"] == "COMPLETED", "work_order_id"
        ]
    )

    assert set(usage["work_order_id"]).issubset(completed_ids)


def test_quantity_and_cost_calculations(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=50)

    assert (usage["quantity_used"] > 0).all()
    assert (usage["unit_cost"] > 0).all()

    expected_cost = (
        usage["quantity_used"] * usage["unit_cost"]
    ).round(2)

    assert (usage["total_cost"] == expected_cost).all()


def test_generation_is_reproducible(work_orders, parts):
    first = generate_parts_usage(work_orders, parts, 25, seed=123)
    second = generate_parts_usage(work_orders, parts, 25, seed=123)

    pd.testing.assert_frame_equal(first, second)


def test_zero_usage_count_returns_empty_table(work_orders, parts):
    usage = generate_parts_usage(work_orders, parts, usage_count=0)

    assert usage.empty
    assert "usage_id" in usage.columns


def test_rejects_negative_usage_count(work_orders, parts):
    with pytest.raises(ValueError, match="zero or greater"):
        generate_parts_usage(work_orders, parts, usage_count=-1)


def test_rejects_empty_work_orders(parts):
    with pytest.raises(ValueError, match="work_orders must not be empty"):
        generate_parts_usage(pd.DataFrame(), parts)


def test_rejects_empty_parts(work_orders):
    with pytest.raises(ValueError, match="parts must not be empty"):
        generate_parts_usage(work_orders, pd.DataFrame())


def test_rejects_missing_work_order_columns(parts):
    invalid_orders = pd.DataFrame({"id": ["WO-001"]})

    with pytest.raises(ValueError, match="work_order_id and status"):
        generate_parts_usage(invalid_orders, parts)


def test_rejects_duplicate_part_ids(work_orders):
    duplicate_parts = pd.DataFrame(
        {
            "part_id": ["PART-001", "PART-001"],
            "unit_cost": [100.0, 150.0],
        }
    )

    with pytest.raises(ValueError, match="must be unique"):
        generate_parts_usage(work_orders, duplicate_parts)


def test_rejects_work_orders_without_completed_orders(parts):
    scheduled_orders = pd.DataFrame(
        {
            "work_order_id": ["WO-001"],
            "status": ["SCHEDULED"],
        }
    )

    with pytest.raises(ValueError, match="COMPLETED work order"):
        generate_parts_usage(scheduled_orders, parts, usage_count=1)
