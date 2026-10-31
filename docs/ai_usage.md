# Business Rules

## 1. Data Generation

- Dataset generation supports a configurable random seed for reproducibility.
- Master data is generated for plants, production lines, machines, sensors,
  technicians, operating shifts, parts, and maintenance-related records.
- Entity relationships must reference valid identifiers.
- Dataset validation must reject invalid relationships before export.
- Failure events are exported separately as ground truth.

## 2. Telemetry Generation

- Telemetry is generated at a configurable interval.
- The interval must be positive and divide evenly into 1,440 minutes.
- The simulation requires at least one day.
- Sensor IDs and machine IDs must be unique and non-null.
- Every sensor must reference a valid machine.
- Sensor types must be supported by the generator.
- Sensor units must match the configured sensor profile.
- Generated readings are clipped to the sensor profile's minimum and maximum.
- Scheduled shutdown periods produce zero readings and a SHUTDOWN quality status.
- Normal readings use deterministic random streams derived from the seed.

## 3. Failure Precursors

The synthetic generator models precursor signals for the following failure types:

| Failure type        | Affected sensor type | Simulated direction    |
| ------------------- | -------------------- | ---------------------- |
| OVERHEATING         | TEMP                 | Increasing temperature |
| EXCESSIVE_VIBRATION | VIBRATION            | Increasing vibration   |
| BEARING_WEAR        | VIBRATION            | Increasing vibration   |
| PRESSURE_LOSS       | PRESSURE             | Decreasing pressure    |
| ELECTRICAL_FAULT    | CURRENT              | Increasing current     |

- Precursors are simulated before the associated failure.
- The precursor duration is configurable.
- Unrelated sensor types should not receive failure-specific precursor signals.
- Overlapping precursor events use the strongest relevant signal rather than
  summing all precursor effects.
- Ground-truth failure labels are kept separate from telemetry.

## 4. Risk Scoring

- Risk scores are bounded between 0 and 100.
- Only readings with operating state RUNNING contribute to risk scoring.
- Sensor-specific warning and critical thresholds are defined in the risk-scoring module.
- Higher temperature, vibration, and current readings increase risk under the
  current scoring rules.
- Lower pressure readings increase risk under the current scoring rules.
- Machine risk is derived from the maximum sensor risk calculated for that machine.
- Risk levels are assigned using the scoring module's configured score bands.

Thresholds are synthetic assumptions for this project, not certified industrial
safety thresholds.

## 5. Prediction Evaluation

- A prediction is considered positive when its risk score meets or exceeds the
  configured risk threshold.
- A future failure is positive ground truth when its timestamp is strictly later
  than the prediction timestamp and falls within the prediction horizon.
- A failure at the exact prediction timestamp is not counted as a future failure.
- Evaluation reports precision, recall, F1-score, accuracy, and confusion-matrix counts.
- Evaluation metrics must be interpreted alongside class imbalance and missed failures.

## 6. Limitations

- Synthetic precursor patterns do not establish real-world predictive accuracy.
- The current scoring thresholds require calibration against real equipment data.
- Evaluation performance may be affected by precursor duration, event timing,
  class imbalance, and how repeated failures are labelled.
- Results should not be used alone to make safety-critical maintenance decisions.
