
import pandas as pd
import pytest

from failure_risk.risk_scoring import calculate_risk_scores


def make_telemetry(sensor_type, value, state="RUNNING"):
    return pd.DataFrame(
        [{
            "machine_id": "M-001",
            "sensor_type": sensor_type,
            "timestamp": "2026-01-01T10:00:00",
            "value": value,
            "operating_state": state,
        }]
    )


def test_normal_temperature_has_low_risk():
    result = calculate_risk_scores(make_telemetry("TEMP", 65.0))

    assert result.loc[0, "risk_score"] == 0
    assert result.loc[0, "risk_level"] == "LOW"


def test_critical_temperature_has_critical_risk():
    result = calculate_risk_scores(make_telemetry("TEMP", 110.0))

    assert result.loc[0, "risk_score"] == 100
    assert result.loc[0, "risk_level"] == "CRITICAL"


def test_low_pressure_increases_risk():
    result = calculate_risk_scores(make_telemetry("PRESSURE", 100.0))

    assert result.loc[0, "risk_score"] == 100
    assert result.loc[0, "risk_level"] == "CRITICAL"


def test_shutdown_readings_are_ignored():
    result = calculate_risk_scores(
        make_telemetry("TEMP", 110.0, state="STOPPED")
    )

    assert result.empty


def test_missing_required_column_raises_error():
    with pytest.raises(ValueError, match="missing required columns"):
        calculate_risk_scores(pd.DataFrame({"machine_id": ["M-001"]}))
