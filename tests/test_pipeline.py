
from unittest.mock import patch

from failure_risk import pipeline

from pathlib import Path

import pandas as pd

from failure_risk.pipeline import generate_dataset, export_dataset

import pytest


def test_generate_dataset_contains_expected_tables():
    data = generate_dataset(days=1)

    expected = {
        "plants",
        "production_lines",
        "machines",
        "sensors",
        "failure_events",
        "maintenance_work_orders",
        "technicians",
        "operating_shifts",
        "parts",
        "parts_usage",
    }

    assert set(data.keys()) == expected


def test_generate_dataset_is_reproducible():
    first = generate_dataset(days=1, seed=12345)
    second = generate_dataset(days=1, seed=12345)

    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])


def test_export_dataset_separates_ground_truth(tmp_path):
    data = generate_dataset(days=1)

    raw_dir = tmp_path / "raw"
    truth_dir = tmp_path / "ground_truth"

    exported = export_dataset(
        data,
        output_dir=str(raw_dir),
        ground_truth_dir=str(truth_dir),
    )

    assert len(exported) == 10
    assert (truth_dir / "failure_events.csv").exists()
    assert not (raw_dir / "failure_events.csv").exists()

    for name in data:
        if name != "failure_events":
            assert (raw_dir / f"{name}.csv").exists()


def test_exported_csv_preserves_row_counts(tmp_path):
    data = generate_dataset(days=1)

    exported = export_dataset(
        data,
        output_dir=str(tmp_path / "raw"),
        ground_truth_dir=str(tmp_path / "ground_truth"),
    )

    for name, path in exported.items():
        exported_df = pd.read_csv(Path(path))
        assert len(exported_df) == len(data[name])


def test_write_dataset_telemetry_passes_failure_type(tmp_path):
    data = generate_dataset(
        plants_count=1,
        lines_count=1,
        machines_count=2,
        sensors_count=4,
        failures_count=100,
        days=1,
        seed=12345,
    )

    failure = data["failure_events"].iloc[0]
    captured = {}

    def fake_write_telemetry_csv(**kwargs):
        captured.update(kwargs)
        return 0

    with patch.object(
        pipeline,
        "write_telemetry_csv",
        side_effect=fake_write_telemetry_csv,
    ):
        result = pipeline.write_dataset_telemetry(
            data,
            output_path=str(tmp_path / "telemetry.csv"),
            days=1,
        )

    assert result == 0

    schedule = captured["failure_schedule"]
    machine_id = failure["machine_id"]

    assert machine_id in schedule
    assert schedule[machine_id]["timestamp"] == failure["failure_timestamp"]
    assert schedule[machine_id]["failure_type"] == failure["failure_type"]

def test_export_dataset_rejects_invalid_data(tmp_path):
    data = generate_dataset(days=1, seed=12345)

    data["machines"].loc[0, "line_id"] = "LINE-DOES-NOT-EXIST"

    raw_dir = tmp_path / "raw"
    truth_dir = tmp_path / "ground_truth"

    with pytest.raises(ValueError, match="Dataset validation failed"):
        export_dataset(
            data,
            output_dir=str(raw_dir),
            ground_truth_dir=str(truth_dir),
        )

    assert not (raw_dir / "machines.csv").exists()
    assert not (truth_dir / "failure_events.csv").exists()
