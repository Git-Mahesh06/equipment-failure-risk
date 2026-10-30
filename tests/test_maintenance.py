
import pandas as pd
import pytest

from failure_risk.generators.maintenance import (
    generate_maintenance_work_orders,
)


def sample_machines():
    return pd.DataFrame(
        {"machine_id": ["MACH-0001", "MACH-0002", "MACH-0003"]}
    )


def test_work_order_and_technician_counts():
    orders, technicians = generate_maintenance_work_orders(
        sample_machines(),
        work_orders_count=50,
        technicians_count=5,
    )

    assert len(orders) == 50
    assert len(technicians) == 5


def test_work_order_ids_are_unique():
    orders, _ = generate_maintenance_work_orders(sample_machines())

    assert orders["work_order_id"].is_unique


def test_machine_and_technician_references_are_valid():
    machines = sample_machines()
    orders, technicians = generate_maintenance_work_orders(machines)

    assert set(orders["machine_id"]).issubset(set(machines["machine_id"]))
    assert set(orders["technician_id"]).issubset(
        set(technicians["technician_id"])
    )


def test_planned_end_is_not_before_planned_start():
    orders, _ = generate_maintenance_work_orders(sample_machines())

    assert (orders["planned_end"] >= orders["planned_start"]).all()


def test_completed_orders_have_actual_end():
    orders, _ = generate_maintenance_work_orders(sample_machines())
    completed = orders[orders["status"] == "COMPLETED"]

    assert completed["actual_end"].notna().all()


def test_generation_is_reproducible():
    first_orders, first_technicians = (
        generate_maintenance_work_orders(sample_machines(), seed=123)
    )
    second_orders, second_technicians = (
        generate_maintenance_work_orders(sample_machines(), seed=123)
    )

    pd.testing.assert_frame_equal(first_orders, second_orders)
    pd.testing.assert_frame_equal(first_technicians, second_technicians)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"work_orders_count": 0},
        {"technicians_count": 0},
        {"days": 0},
    ],
)
def test_invalid_counts_are_rejected(kwargs):
    with pytest.raises(ValueError):
        generate_maintenance_work_orders(sample_machines(), **kwargs)


def test_empty_machine_table_is_rejected():
    with pytest.raises(ValueError):
        generate_maintenance_work_orders(
            pd.DataFrame({"machine_id": []})
        )
