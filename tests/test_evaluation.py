
import pandas as pd
import pytest

from failure_risk.evaluation import evaluate_predictions


def test_evaluation_metrics_for_seven_day_window():
    predictions = pd.DataFrame([
        {"machine_id": "M1", "prediction_timestamp": "2026-01-01", "risk_score": 80},
        {"machine_id": "M2", "prediction_timestamp": "2026-01-01", "risk_score": 80},
        {"machine_id": "M3", "prediction_timestamp": "2026-01-01", "risk_score": 20},
        {"machine_id": "M4", "prediction_timestamp": "2026-01-01", "risk_score": 20},
    ])

    failures = pd.DataFrame([
        {"machine_id": "M1", "failure_timestamp": "2026-01-05"},
        {"machine_id": "M3", "failure_timestamp": "2026-01-05"},
        # This failure is outside the seven-day window for M4.
        {"machine_id": "M4", "failure_timestamp": "2026-01-10"},
    ])

    result = evaluate_predictions(predictions, failures)

    assert result["prediction_window_days"] == 7
    assert result["samples"] == 4
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1_score"] == 0.5
    assert result["accuracy"] == 0.5
    assert result["confusion_matrix"] == {
        "true_positive": 1,
        "true_negative": 1,
        "false_positive": 1,
        "false_negative": 1,
    }


def test_failure_at_prediction_time_is_not_a_future_failure():
    predictions = pd.DataFrame([
        {"machine_id": "M1", "prediction_timestamp": "2026-01-01", "risk_score": 20},
    ])
    failures = pd.DataFrame([
        {"machine_id": "M1", "failure_timestamp": "2026-01-01"},
    ])

    result = evaluate_predictions(predictions, failures)

    assert result["confusion_matrix"]["true_negative"] == 1


def test_empty_predictions_raise_error():
    predictions = pd.DataFrame(
        columns=["machine_id", "prediction_timestamp", "risk_score"]
    )
    failures = pd.DataFrame(
        columns=["machine_id", "failure_timestamp"]
    )

    with pytest.raises(ValueError, match="predictions must not be empty"):
        evaluate_predictions(predictions, failures)


def test_invalid_prediction_window_raises_error():
    predictions = pd.DataFrame([
        {"machine_id": "M1", "prediction_timestamp": "2026-01-01", "risk_score": 20},
    ])
    failures = pd.DataFrame(
        columns=["machine_id", "failure_timestamp"]
    )

    with pytest.raises(ValueError, match="prediction_window_days"):
        evaluate_predictions(
            predictions, failures, prediction_window_days=0
        )
