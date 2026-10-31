
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from failure_risk.evaluation import evaluate_predictions
from failure_risk.risk_scoring import calculate_risk_scores



def generate_daily_predictions(
    telemetry_path: str | Path,
    sensors: pd.DataFrame,
    days: int,
    interval_minutes: int,
    start_time: str = "2026-01-01T00:00:00",
    prediction_window_days: int = 7,
    chunksize: int = 100_000,
) -> pd.DataFrame:
    """Generate daily point-in-time predictions from recent telemetry."""
    if days <= prediction_window_days:
        raise ValueError("Telemetry days must exceed the prediction window.")
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive.")

    required_sensor_columns = {"sensor_id", "sensor_type"}
    missing = required_sensor_columns - set(sensors.columns)
    if missing:
        raise ValueError(
            f"Sensor metadata is missing columns: {sorted(missing)}"
        )

    if sensors["sensor_id"].isna().any() or sensors["sensor_id"].duplicated().any():
        raise ValueError("Sensor IDs must be non-null and unique.")

    sensor_types = sensors.set_index("sensor_id")["sensor_type"].to_dict()
    start = pd.Timestamp(start_time)
    end = start + pd.Timedelta(days=days)
    last_observed_time = end - pd.Timedelta(minutes=interval_minutes)
    last_prediction_time = (
        last_observed_time - pd.Timedelta(days=prediction_window_days)
    )

    columns = [
        "sensor_id",
        "machine_id",
        "timestamp",
        "operating_state",
        "value",
    ]
    chunks = []

    for chunk in pd.read_csv(
        telemetry_path,
        usecols=columns,
        chunksize=chunksize,
    ):
        chunk["timestamp"] = pd.to_datetime(
            chunk["timestamp"], errors="raise"
        )
        chunk = chunk[
            (chunk["timestamp"] >= start)
            & (chunk["timestamp"] <= last_prediction_time)
        ].copy()

        if chunk.empty:
            continue

        chunk["sensor_type"] = chunk["sensor_id"].map(sensor_types)
        if chunk["sensor_type"].isna().any():
            unknown = chunk.loc[
                chunk["sensor_type"].isna(), "sensor_id"
            ].unique()
            raise ValueError(
                f"Unknown sensor IDs found in telemetry: {unknown[:5]}"
            )

        chunks.append(chunk)

    if not chunks:
        raise ValueError("No telemetry was found in the prediction period.")

    telemetry = pd.concat(chunks, ignore_index=True)
    prediction_times = pd.date_range(
        start=start,
        end=last_prediction_time,
        freq="D",
    )

    predictions = []

    for timestamp in prediction_times:
        window_start = timestamp - pd.Timedelta(hours=24)
        window = telemetry[
            (telemetry["timestamp"] > window_start)
            & (telemetry["timestamp"] <= timestamp)
        ]

        if window.empty:
            continue

        scores = calculate_risk_scores(window)
        if scores.empty:
            continue

        scores["prediction_timestamp"] = timestamp
        predictions.append(scores)

    if not predictions:
        raise ValueError("No machine risk predictions could be generated.")

    return pd.concat(predictions, ignore_index=True)



def evaluate_and_save_predictions(
    predictions: pd.DataFrame,
    failure_events: pd.DataFrame,
    output_dir: str | Path = "data/reports",
    prediction_window_days: int = 7,
    risk_threshold: float = 50.0,
) -> dict:
    """Save predictions and evaluation metrics."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metrics = evaluate_predictions(
        predictions=predictions,
        failure_events=failure_events,
        prediction_window_days=prediction_window_days,
        risk_threshold=risk_threshold,
    )

    predictions_file = output_path / "risk_predictions.csv"
    metrics_file = output_path / "risk_evaluation.json"

    predictions.to_csv(predictions_file, index=False)

    with metrics_file.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print(f"Risk predictions: {predictions_file}")
    print(f"Evaluation metrics: {metrics_file}")
    print(f"Evaluation samples: {metrics['samples']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 score: {metrics['f1_score']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")

    return metrics
