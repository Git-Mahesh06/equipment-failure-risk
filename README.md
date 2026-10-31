# Equipment Failure Risk Prediction Pipeline

## 1. Project Overview

The Equipment Failure Risk Prediction Pipeline is a reproducible Python data
engineering project that generates synthetic industrial data, simulates sensor
telemetry and failure precursors, validates data quality, calculates equipment
failure-risk scores, and evaluates predictions against failure-event ground truth.

The project was developed as part of the YottaFlex AI candidate coding challenge.

## 2. Problem Statement

Industrial equipment can exhibit warning signs before failure, including
increasing temperature, abnormal vibration, pressure loss, and changes in
electrical current.

This project builds a pipeline to:

- Generate interconnected industrial master and operational datasets.
- Simulate sensor telemetry, operating states, and failure-related patterns.
- Maintain separate failure-event ground truth.
- Validate entity relationships and data quality.
- Identify elevated equipment risk using documented scoring rules.
- Evaluate predictions against simulated failure events.
- Export datasets and machine-readable reports.
- Support reproducible generation through a configurable random seed.

## 3. Implementation Status

The core pipeline and automated tests have been implemented.

### Implemented

- Configurable synthetic dataset generation.
- Plants, production lines, machines, sensors, and related operational entities.
- Deterministic data generation using a configurable random seed.
- Primary-key, foreign-key, and dataset validation.
- Streaming telemetry generation.
- Simulated machine shutdowns and sensor-specific failure precursors.
- Separate export of failure-event ground truth.
- Telemetry validation and exception reporting.
- Machine-level risk scoring.
- Prediction evaluation with precision, recall, F1-score, accuracy, and confusion-matrix counts.
- CSV and JSON output generation.
- Automated tests for generation, validation, telemetry, risk scoring, and evaluation.

### Validation Evidence

The full automated test suite reported **103 passed in 1.96 seconds**.

An earlier full pipeline execution generated:

- 100 machines.
- 500 sensors.
- 150 failure events.
- 2,160,000 telemetry readings.
- Zero telemetry validation errors.
- 864 telemetry warnings.

The warnings were reported by the telemetry validation stage and should be reviewed as part of data-quality analysis.

The evaluation figures recorded below are from an earlier execution and should not be assumed to represent a later regenerated dataset.

## 4. Technology Stack

- **Python 3.12:** Pipeline implementation.
- **pandas:** Structured data processing and analysis.
- **NumPy:** Numerical operations and synthetic signal generation.
- **PyYAML:** Configuration loading.
- **pytest:** Automated testing.
- **CSV:** Dataset and prediction exports.
- **JSON:** Evaluation and machine-readable reports.
- **Git and GitHub:** Version control and source-code hosting.

The current implementation uses CSV and JSON outputs. PostgreSQL is not required to run the documented pipeline.

## 5. Dataset Configuration

The full configuration in `config/config.yaml` specifies:

| Setting               | Configured value |
| --------------------- | ---------------: |
| Plants                |                3 |
| Production lines      |               12 |
| Machines              |              100 |
| Sensors               |              500 |
| Telemetry history     |          90 days |
| Telemetry interval    |       30 minutes |
| Target failure events |              150 |
| Random seed           |       `20261022` |

With 500 sensors, 90 days, and a 30-minute interval, the expected telemetry count is:

500 sensors × 90 days × 48 readings per day = 2,160,000 readings.

Actual output counts should be checked against the generated files and pipeline logs.

## 6. Core Data Entities

The project generates data for:

1. Plants
2. Production lines
3. Machines
4. Sensors
5. Telemetry readings
6. Failure events
7. Maintenance work orders
8. Technicians
9. Operating shifts
10. Parts and parts usage

Dataset relationships and field definitions are documented in `docs/data_dictionary.md`.
Business and simulation assumptions are documented in `docs/business_rules.md`.

Failure events are retained separately as ground truth rather than included as
ordinary telemetry prediction features.

## 7. Pipeline Workflow

The pipeline follows this general workflow:

1. Load configuration.
2. Generate master and operational datasets.
3. Validate dataset structure and relationships.
4. Export structured datasets, keeping failure-event ground truth separate.
5. Generate timestamped sensor telemetry.
6. Validate telemetry and report data-quality exceptions.
7. Calculate machine-level risk predictions.
8. Compare predictions against future failure events.
9. Export risk predictions and evaluation metrics.

The implementation is organized into modules for data generation, validation,
telemetry, risk scoring, evaluation, and command-line execution.

## 8. Data Quality and Exception Handling

The pipeline includes validation for data structure and relationships, as well
as telemetry-specific checks.

The telemetry generator enforces rules such as:

- Sensor identifiers must be unique and non-null.
- Machine identifiers must be unique and non-null.
- Sensors must reference valid machines.
- Sensor types and units must be supported.
- The telemetry interval must be positive and divide evenly into one day.
- Generated values are clipped to their sensor profile's physical bounds.
- Scheduled shutdowns are represented explicitly through operating state and
  quality status.

Telemetry validation can report errors and warnings. A successful generation
run does not mean that every generated record is warning-free.

See `docs/business_rules.md` for the documented simulation rules and limitations.

## 9. Risk Scoring and Evaluation

The risk-scoring module uses sensor-specific thresholds to calculate risk scores
between 0 and 100. The current scoring logic assigns higher risk to elevated
temperature, vibration, and current readings, and to low pressure readings.

Predictions are evaluated against failure events occurring strictly after the
prediction timestamp and within the configured prediction horizon.

### Latest Full-Scale Execution

The latest full-scale pipeline execution completed successfully using the configured random seed `20261022`.

| Metric                        |    Result |
| ----------------------------- | --------: |
| Machines                      |       100 |
| Sensors                       |       500 |
| Failure events                |       150 |
| Telemetry readings            | 2,160,000 |
| Evaluation samples            |     8,300 |
| Precision                     |    0.9000 |
| Recall                        |    0.0098 |
| F1-score                      |    0.0194 |
| Accuracy                      |    0.8902 |
| Telemetry validation errors   |         0 |
| Telemetry validation warnings |     1,587 |

The automated test suite passed with **103 tests**.

The evaluation results show high precision but very low recall. The current risk-scoring approach misses most failure-positive cases, so its predictive performance requires further improvement before real-world use. Accuracy should not be interpreted in isolation.

The telemetry validation stage reported 1,587 warnings and zero errors. The warnings should be investigated and explained in the data-quality documentation.

These results are from the latest recorded full-scale execution; future code or configuration changes may alter them.

**Important:** These are historical evaluation figures. Rerun the evaluation
after any changes to telemetry generation or risk scoring before describing
them as final results.

## 10. Running the Project

Run the following commands from the repository root in an activated Python
virtual environment.

### Install dependencies

```powershell
python -m pip install -e .
```

If development dependencies are managed separately in your environment,
install the appropriate test dependencies as well.

### Run the full pipeline

```powershell
python -m failure_risk.cli --config config/config.yaml
```

The pipeline reads the configuration, generates datasets and telemetry,
performs validation, creates risk predictions, and writes evaluation outputs.

### Run the automated tests

```powershell
python -m pytest -q
```

The latest recorded full test run reported 103 passing tests. Run the command
again on the final code revision to verify the submitted version.

## 11. Output Files

The configured output locations include:

- `data/generated/` — generated structured datasets.
- `data/ground_truth/` — failure-event ground truth.
- `data/exceptions/` — data-quality exception outputs.
- `data/reports/risk_predictions.csv` — machine risk predictions.
- `data/reports/risk_evaluation.json` — prediction evaluation metrics.

The exact output files depend on the configured pipeline and the outputs produced
by the current code. Inspect the generated directories after execution.

Generated data and reports may be excluded from version control according to
the repository's `.gitignore` rules.

## 12. Reproducibility

A configurable random seed is used to support repeatable synthetic data
generation.

Automated tests cover reproducibility and selected data-integrity rules.
Reproducibility should be verified by comparing outputs generated using the
same configuration and seed.

Changes to the generator, configuration, or scoring logic may change the
generated outputs and evaluation results.

## 13. Assumptions and Limitations

- The dataset is synthetic and does not represent measured industrial equipment.
- Sensor thresholds and precursor patterns are simulation assumptions.
- The risk-scoring rules are not a trained or production-validated predictive model.
- Synthetic performance does not establish real-world failure prediction accuracy.
- The earlier evaluation showed very low recall and a substantial number of missed
  positive cases.
- The pipeline should not be used alone to make safety-critical maintenance
  decisions.
- Further calibration, feature engineering, validation against real operational
  data, and evaluation across different conditions would be required for
  production use.

## 14. AI-Assisted Development Disclosure

LLM tools assisted with project planning, implementation guidance, debugging,
test design, and documentation.

The developer remains responsible for reviewing changes, executing the code,
checking test results, and validating the final submission.

The assistance summary and limitations are documented in `docs/ai_usage.md`.
A summary of development prompts and outcomes is maintained in
`prompts/prompt_history.md`.

## 15. Repository Structure

```text
equipment-failure-risk/
├── config/
│   └── config.yaml
├── docs/
│   ├── ai_usage.md
│   ├── business_rules.md
│   └── data_dictionary.md
├── prompts/
│   └── prompt_history.md
├── scripts/
├── src/
│   └── failure_risk/
├── tests/
├── README.md
└── pyproject.toml
```

This is a high-level overview; consult the repository for the complete module
and test structure.

## 16. Submission Status

The core implementation, full-scale pipeline execution, model evaluation, and automated testing have been completed.

- **Automated tests:** 103 passed in the latest recorded full-suite run.
- **Pipeline execution:** Completed successfully, processing 2,160,000 telemetry records.
- **Data validation:** Completed, with zero telemetry errors and 1,587 warnings.
- **Model evaluation:** Completed on 8,300 samples.
- **Evaluation metrics:** Accuracy: 89.02%, Precision: 90.00%, Recall: 1.00%, F1 Score: 1.94%.
- **Version control:** Code committed and pushed to GitHub.

**Submission status:** The implementation has been committed to GitHub and submitted for evaluation.
