
import pandas as pd
import pytest

from failure_risk.generators.failure_events import generate_failure_events


def sample_machines():
    return pd.DataFrame(
        {
            "machine_id": ["MACH-0001", "MACH-0002", "MACH-0003"],
        }
    )


def test_failure_count_is_within_requested_range():
    failures = generate_failure_events(
        sample_machines(),
        failures_count=120,
        seed=123,
    )

    assert len(failures) == 120


def test_failure_ids_are_unique():
    failures = generate_failure_events(sample_machines(), seed=123)

    assert failures["failure_id"].is_unique


def test_every_failure_references_a_valid_machine():
    machines = sample_machines()
    failures = generate_failure_events(machines, seed=123)

    assert set(failures["machine_id"]).issubset(
        set(machines["machine_id"])
    )


def test_failure_timestamps_are_inside_window():
    start = pd.Timestamp("2026-01-01T00:00:00")
    end = start + pd.Timedelta(days=90)

    failures = generate_failure_events(
        sample_machines(),
        start_time="2026-01-01T00:00:00",
        days=90,
        seed=123,
    )

    assert (failures["failure_timestamp"] >= start).all()
    assert (failures["failure_timestamp"] < end).all()


def test_generation_is_reproducible():
    first = generate_failure_events(sample_machines(), seed=123)
    second = generate_failure_events(sample_machines(), seed=123)

    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize("count", [99, 201, 0, -1])
def test_invalid_failure_count_is_rejected(count):
    with pytest.raises(ValueError):
        generate_failure_events(
            sample_machines(),
            failures_count=count,
        )


def test_empty_machine_list_is_rejected():
    with pytest.raises(ValueError):
        generate_failure_events(
            pd.DataFrame({"machine_id": []})
        )
