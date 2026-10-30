
import pandas as pd

from failure_risk.telemetry_validation import (
    validate_telemetry,
    write_exception_report,
)


def sample_telemetry():
    return pd.DataFrame({
        "telemetry_id": ["T001", "T002"],
        "machine_id": ["M001", "M001"],
        "sensor_id": ["S001", "S001"],
        "timestamp": [
            "2026-01-01T00:00:00",
            "2026-01-01T00:30:00",
        ],
        "value": [65.0, 66.0],
    })


def test_valid_telemetry_has_no_exceptions():
    exceptions = validate_telemetry(sample_telemetry())
    assert exceptions == []


def test_duplicate_telemetry_ids_are_detected():
    telemetry = sample_telemetry()
    telemetry.loc[1, "telemetry_id"] = "T001"

    exceptions = validate_telemetry(telemetry)

    assert any(
        item["exception_type"] == "DUPLICATE_TELEMETRY_ID"
        for item in exceptions
    )



def test_invalid_reading_is_detected():
    telemetry = sample_telemetry()
    telemetry["value"] = telemetry["value"].astype(object)
    telemetry.loc[0, "value"] = "invalid"

    exceptions = validate_telemetry(telemetry)

    assert any(
        item["exception_type"] == "INVALID_READING"
        for item in exceptions
    )



def test_unknown_machine_is_detected():
    telemetry = sample_telemetry()
    telemetry.loc[0, "machine_id"] = "UNKNOWN"

    machines = pd.DataFrame({"machine_id": ["M001"]})

    exceptions = validate_telemetry(telemetry, machines=machines)

    assert any(
        item["exception_type"] == "UNKNOWN_MACHINE"
        for item in exceptions
    )


def test_exception_report_is_written(tmp_path):
    exceptions = [{
        "exception_type": "INVALID_READING",
        "severity": "ERROR",
        "row_index": "0",
        "message": "Telemetry reading is not numeric.",
    }]

    output = tmp_path / "exceptions.csv"
    write_exception_report(exceptions, output)

    report = pd.read_csv(output)

    assert len(report) == 1
    assert report.loc[0, "exception_type"] == "INVALID_READING"
