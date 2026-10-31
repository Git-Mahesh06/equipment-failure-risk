
from __future__ import annotations

import pandas as pd


def evaluate_predictions(
    predictions: pd.DataFrame,
    failure_events: pd.DataFrame,
    prediction_window_days: int = 7,
    risk_threshold: float = 50.0,
) -> dict:
    """Evaluate timestamped machine risk scores against future failures.

    A prediction is positive when risk_score >= risk_threshold.
    A ground-truth label is positive when at least one failure occurs
    strictly after prediction_timestamp and within the next N days.

    Each prediction row is one machine-at-a-time evaluation sample.
    """

    if prediction_window_days <= 0:
        raise ValueError("prediction_window_days must be greater than zero.")

    prediction_required = {
        "machine_id",
        "prediction_timestamp",
        "risk_score",
    }
    failure_required = {"machine_id", "failure_timestamp"}

    missing_predictions = prediction_required - set(predictions.columns)
    if missing_predictions:
        raise ValueError(
            "Predictions are missing required columns: "
            f"{sorted(missing_predictions)}"
        )

    missing_failures = failure_required - set(failure_events.columns)
    if missing_failures:
        raise ValueError(
            "Failure events are missing required columns: "
            f"{sorted(missing_failures)}"
        )

    if predictions.empty:
        raise ValueError("predictions must not be empty.")

    pred = predictions[list(prediction_required)].copy()
    failures = failure_events[list(failure_required)].copy()

    pred["prediction_timestamp"] = pd.to_datetime(
        pred["prediction_timestamp"], errors="raise"
    )
    failures["failure_timestamp"] = pd.to_datetime(
        failures["failure_timestamp"], errors="raise"
    )
    pred["risk_score"] = pd.to_numeric(pred["risk_score"], errors="raise")

    if pred["machine_id"].isna().any():
        raise ValueError("Prediction machine_id values must not be null.")

    if failures["machine_id"].isna().any():
        raise ValueError("Failure machine_id values must not be null.")

    if not pred["risk_score"].between(0, 100).all():
        raise ValueError("risk_score values must be between 0 and 100.")

    # The target is a failure in (prediction time, prediction time + 7 days].
    failure_times = {
        machine_id: group["failure_timestamp"].sort_values().tolist()
        for machine_id, group in failures.groupby("machine_id")
    }
    horizon = pd.Timedelta(days=prediction_window_days)

    actual_labels: list[int] = []
    predicted_labels: list[int] = []

    for row in pred.itertuples(index=False):
        timestamp = row.prediction_timestamp
        future_limit = timestamp + horizon

        has_future_failure = any(
            timestamp < failure_time <= future_limit
            for failure_time in failure_times.get(row.machine_id, [])
        )

        actual_labels.append(int(has_future_failure))
        predicted_labels.append(int(row.risk_score >= risk_threshold))

    tp = sum(a == 1 and p == 1 for a, p in zip(actual_labels, predicted_labels))
    tn = sum(a == 0 and p == 0 for a, p in zip(actual_labels, predicted_labels))
    fp = sum(a == 0 and p == 1 for a, p in zip(actual_labels, predicted_labels))
    fn = sum(a == 1 and p == 0 for a, p in zip(actual_labels, predicted_labels))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    accuracy = (tp + tn) / len(pred)

    return {
        "prediction_window_days": prediction_window_days,
        "risk_threshold": risk_threshold,
        "samples": len(pred),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "confusion_matrix": {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        },
    }
