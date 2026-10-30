
import pandas as pd
from pandas.testing import assert_frame_equal

from src.failure_risk.generators.master_data import generate_master_data
from src.failure_risk.generators.telemetry import iter_telemetry_chunks


def small_data():
    data = generate_master_data(
        plants_count=1,
        lines_count=1,
        machines_count=2,
        sensors_count=4,
        seed=20261022,
    )
    return data["sensors"], data["machines"]


def test_telemetry_row_count():
    sensors, machines = small_data()

    chunks = list(iter_telemetry_chunks(
        sensors,
        machines,
        start_time="2026-01-01T00:00:00",
        days=1,
        interval_minutes=60,
    ))

    assert sum(len(chunk) for chunk in chunks) == 4 * 24


def test_telemetry_ids_are_unique():
    sensors, machines = small_data()

    chunks = list(iter_telemetry_chunks(
        sensors,
        machines,
        days=1,
        interval_minutes=60,
    ))

    telemetry = pd.concat(chunks, ignore_index=True)

    assert telemetry["telemetry_id"].is_unique


def test_telemetry_references_valid_sensors_and_machines():
    sensors, machines = small_data()

    chunks = list(iter_telemetry_chunks(
        sensors,
        machines,
        days=1,
        interval_minutes=60,
    ))

    telemetry = pd.concat(chunks, ignore_index=True)

    assert set(telemetry["sensor_id"]).issubset(
        set(sensors["sensor_id"])
    )
    assert set(telemetry["machine_id"]).issubset(
        set(machines["machine_id"])
    )


def test_telemetry_is_reproducible():
    sensors, machines = small_data()

    def generate():
        return list(iter_telemetry_chunks(
            sensors,
            machines,
            start_time="2026-01-01T00:00:00",
            days=1,
            interval_minutes=60,
            seed=12345,
        ))

    first = generate()
    second = generate()

    assert len(first) == len(second)

    for left, right in zip(first, second):
        assert_frame_equal(left, right)



def test_failure_precursor_increases_temperature():
    sensors, machines = small_data()

    temperature_sensor = sensors[
        sensors["sensor_type"] == "TEMP"
    ].iloc[0]

    machine_id = temperature_sensor["machine_id"]

    chunks = list(iter_telemetry_chunks(
        sensors[
            sensors["sensor_id"] == temperature_sensor["sensor_id"]
        ],
        machines,
        start_time="2026-01-01T00:00:00",
        days=2,
        interval_minutes=60,
        seed=12345,
        failure_schedule={
            machine_id: "2026-01-02T00:00:00"
        },
        precursor_hours=24,
    ))

    telemetry = pd.concat(chunks, ignore_index=True)

    running = telemetry[
        telemetry["operating_state"] == "RUNNING"
    ].copy()

    # Normal baseline: 48 to 30 hours before failure.
    before_precursor = running[
        (running["timestamp"] >= pd.Timestamp("2026-01-01T00:00:00"))
        & (running["timestamp"] < pd.Timestamp("2026-01-01T18:00:00"))
    ]

    # Pre-failure period: 6 to 0 hours before failure.
    near_failure = running[
        (running["timestamp"] >= pd.Timestamp("2026-01-01T18:00:00"))
        & (running["timestamp"] < pd.Timestamp("2026-01-02T00:00:00"))
    ]

    assert not before_precursor.empty
    assert not near_failure.empty

    assert (
        near_failure["value"].mean()
        > before_precursor["value"].mean()
    )
