
import pandas as pd
import pytest

from failure_risk.prediction_pipeline import generate_daily_predictions


def test_generate_daily_predictions_maps_sensor_types(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"

    telemetry = pd.DataFrame(
        [
            {
                "sensor_id": "S1",
                "machine_id": "M1",
                "timestamp": timestamp,
                "operating_state": "RUNNING",
                "value": 90.0,
            }
            for timestamp in pd.date_range(
                "2026-01-01", periods=10, freq="D"
            )
        ]
    )
    telemetry.to_csv(telemetry_path, index=False)

    sensors = pd.DataFrame(
        [{"sensor_id": "S1", "sensor_type": "TEMP"}]
    )

    predictions = generate_daily_predictions(
        telemetry_path=telemetry_path,
        sensors=sensors,
        days=10,
        interval_minutes=30,
        prediction_window_days=7,
        chunksize=5,
    )

    assert not predictions.empty
    assert set(predictions["machine_id"]) == {"M1"}
    assert predictions["risk_score"].between(0, 100).all()
    assert predictions["prediction_timestamp"].max() == pd.Timestamp(
    "2026-01-03"
)


def test_generate_daily_predictions_rejects_unknown_sensor(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"

    pd.DataFrame(
        [
            {
                "sensor_id": "UNKNOWN",
                "machine_id": "M1",
                "timestamp": "2026-01-01 00:00:00",
                "operating_state": "RUNNING",
                "value": 90.0,
            }
        ]
    ).to_csv(telemetry_path, index=False)

    sensors = pd.DataFrame(
        [{"sensor_id": "S1", "sensor_type": "TEMP"}]
    )

    with pytest.raises(ValueError, match="Unknown sensor IDs"):
        generate_daily_predictions(
            telemetry_path=telemetry_path,
            sensors=sensors,
            days=10,
            interval_minutes=30,
            prediction_window_days=7,
            chunksize=5,
        )
