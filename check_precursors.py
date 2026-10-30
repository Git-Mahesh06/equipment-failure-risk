import pandas as pd

failures = pd.read_csv(
    "data/ground_truth/failure_events.csv",
    parse_dates=["failure_timestamp"]
)

telemetry = pd.read_csv(
    "data/raw/telemetry.csv",
    usecols=["machine_id", "timestamp", "value",
             "operating_state", "quality_status"],
    parse_dates=["timestamp"]
)

# Use the first failure for each machine.
first_failures = (
    failures.sort_values("failure_timestamp")
    .drop_duplicates("machine_id", keep="first")
)

results = []

for failure in first_failures.itertuples(index=False):
    window_start = failure.failure_timestamp - pd.Timedelta(hours=24)

    window = telemetry[
        (telemetry["machine_id"] == failure.machine_id)
        & (telemetry["timestamp"] >= window_start)
        & (telemetry["timestamp"] < failure.failure_timestamp)
    ]

    results.append({
        "machine_id": failure.machine_id,
        "failure_type": failure.failure_type,
        "readings_24h": len(window),
        "value_std": window["value"].std(),
        "running_readings": int(
            (window["operating_state"] == "RUNNING").sum()
        ),
    })

result = pd.DataFrame(results)

print("Machines with first failure:", len(result))
print("Machines with 24h readings:", int((result["readings_24h"] > 0).sum()))
print("Machines with no readings:", int((result["readings_24h"] == 0).sum()))
print("Average readings in 24h:", round(result["readings_24h"].mean(), 1))
print("\nResults by failure type:")
print(
    result.groupby("failure_type")[
        ["readings_24h", "value_std", "running_readings"]
    ].mean().round(2).to_string()
)
