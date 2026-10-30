
import pandas as pd
import pytest

from failure_risk.generators.operating_shifts import (
    generate_operating_shifts,
)


@pytest.fixture
def machines():
    return pd.DataFrame(
        {
            "machine_id": ["MACH-0001", "MACH-0002"],
        }
    )


def test_generates_three_shifts_per_day(machines):
    shifts = generate_operating_shifts(
        machines,
        start_time="2026-01-01T00:00:00",
        days=2,
    )

    # Two days, three shifts per day, two machines.
    assert len(shifts) == 2 * 3 * 2


def test_shift_ids_are_unique(machines):
    shifts = generate_operating_shifts(machines, days=2)

    assert shifts["shift_id"].is_unique


def test_machine_references_are_valid(machines):
    shifts = generate_operating_shifts(machines, days=2)

    assert set(shifts["machine_id"]) == set(machines["machine_id"])


def test_shift_durations_are_eight_hours(machines):
    shifts = generate_operating_shifts(machines, days=2)

    durations = (
        shifts["shift_end"] - shifts["shift_start"]
    ).dt.total_seconds() / 3600

    assert (durations == 8).all()


def test_night_shift_crosses_midnight(machines):
    shifts = generate_operating_shifts(machines, days=1)

    night = shifts[shifts["shift_name"] == "NIGHT"]

    assert len(night) == len(machines)
    assert (
        night["shift_end"].dt.date
        > night["shift_start"].dt.date
    ).all()


def test_shift_schedule_is_deterministic(machines):
    first = generate_operating_shifts(machines, days=3)
    second = generate_operating_shifts(machines, days=3)

    pd.testing.assert_frame_equal(first, second)


def test_rejects_empty_machines():
    with pytest.raises(ValueError, match="must not be empty"):
        generate_operating_shifts(pd.DataFrame())


def test_rejects_duplicate_machine_ids():
    duplicate_machines = pd.DataFrame(
        {"machine_id": ["MACH-0001", "MACH-0001"]}
    )

    with pytest.raises(ValueError, match="must be unique"):
        generate_operating_shifts(duplicate_machines)


def test_rejects_missing_machine_id_column():
    with pytest.raises(ValueError, match="machine_id column"):
        generate_operating_shifts(pd.DataFrame({"id": ["MACH-0001"]}))


def test_rejects_nonpositive_days(machines):
    with pytest.raises(ValueError, match="greater than zero"):
        generate_operating_shifts(machines, days=0)


def test_filters_shifts_to_observation_window(machines):
    shifts = generate_operating_shifts(
        machines,
        start_time="2026-01-01T12:00:00",
        days=1,
    )

    window_start = pd.Timestamp("2026-01-01T12:00:00")
    window_end = window_start + pd.Timedelta(days=1)

    assert (shifts["shift_end"] > window_start).all()
    assert (shifts["shift_start"] < window_end).all()
