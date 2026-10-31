
from __future__ import annotations

import pandas as pd


# Initial thresholds for the synthetic dataset.
# These are baseline assumptions, not validated industrial limits.
THRESHOLDS = {
    "TEMP": {"warning": 75.0, "critical": 83.0},
    "VIBRATION": {"warning": 6.0, "critical": 11.0},
    "PRESSURE": {"warning": 550.0, "critical": 480.0},
    "CURRENT": {"warning": 55.0, "critical": 65.0},
}

RESULT_COLUMNS = [
    "machine_id",
    "risk_score",
    "prediction_timestamp",
    "risk_level",
]


def calculate_risk_scores(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Calculate baseline machine risk scores from sensor telemetry.

    Only RUNNING readings are considered. The latest reading per
    machine and sensor type is used. Pass a suitable recent time
    window to avoid using readings from after the prediction time.
    """

    required = {
        "machine_id",
        "sensor_type",
        "timestamp",
        "value",
        "operating_state",
    }

    missing = required - set(telemetry.columns)
    if missing:
        raise ValueError(
            f"Telemetry is missing required columns: {sorted(missing)}"
        )

    if telemetry.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    data = telemetry.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="raise"
    )
    data["value"] = pd.to_numeric(
        data["value"], errors="raise"
    )

    data = data[data["operating_state"] == "RUNNING"].copy()

    if data.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    data = data.sort_values("timestamp").drop_duplicates(
        ["machine_id", "sensor_type"],
        keep="last",
    )

    data["sensor_risk"] = 0.0

    for sensor_type, limits in THRESHOLDS.items():
        mask = data["sensor_type"] == sensor_type
        values = data.loc[mask, "value"]

        if sensor_type == "PRESSURE":
            # Lower pressure means higher risk.
            risk = (
                (limits["warning"] - values)
                / (limits["warning"] - limits["critical"])
                * 100
            )
        else:
            # Higher readings mean higher risk for these sensors.
            risk = (
                (values - limits["warning"])
                / (limits["critical"] - limits["warning"])
                * 100
            )

        data.loc[mask, "sensor_risk"] = risk.clip(0, 100)

    result = (
        data.groupby("machine_id", as_index=False)
        .agg(
            risk_score=("sensor_risk", "max"),
            prediction_timestamp=("timestamp", "max"),
        )
    )

    result["risk_score"] = result["risk_score"].round(2)

    result["risk_level"] = pd.cut(
        result["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
    ).astype(str)

    return result[RESULT_COLUMNS]
