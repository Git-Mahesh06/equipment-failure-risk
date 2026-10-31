
import json
from pathlib import Path

import pandas as pd

predictions_path = Path("data/reports/risk_predictions.csv")
failures_path = Path("data/ground_truth/failure_events.csv")

predictions = pd.read_csv(predictions_path)
failures = pd.read_csv(failures_path)

predictions["prediction_timestamp"] = pd.to_datetime(
    predictions["prediction_timestamp"]
)
failures["failure_timestamp"] = pd.to_datetime(
    failures["failure_timestamp"]
)

threshold = 50.0
window = pd.Timedelta(days=7)

failure_times = {
    machine_id: group["failure_timestamp"].sort_values().tolist()
    for machine_id, group in failures.groupby("machine_id")
}

predictions["actual_failure"] = predictions.apply(
    lambda row: int(
        any(
            row["prediction_timestamp"] < failure_time
            <= row["prediction_timestamp"] + window
            for failure_time in failure_times.get(row["machine_id"], [])
        )
    ),
    axis=1,
)

predictions["predicted_failure"] = (
    predictions["risk_score"] >= threshold
).astype(int)

print("\nRisk score distribution:")
print(predictions["risk_score"].describe().round(2))

print("\nRisk scores by actual outcome:")
print(
    predictions.groupby("actual_failure")["risk_score"]
    .agg(["count", "mean", "median", "max"])
    .round(2)
)

print("\nActual failures by risk level:")
print(
    pd.crosstab(
        predictions["actual_failure"],
        predictions["risk_level"],
        margins=True,
    )
)

print("\nMissed failures — score distribution:")
missed = predictions[
    (predictions["actual_failure"] == 1)
    & (predictions["predicted_failure"] == 0)
]
print(missed["risk_score"].describe().round(2))

print("\nSaved evaluation metrics:")
print(
    json.dumps(
        json.loads(
            Path("data/reports/risk_evaluation.json").read_text(
                encoding="utf-8"
            )
        ),
        indent=2,
    )
)
