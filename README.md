# Equipment Failure Risk Prediction Pipeline

## 1. Project Overview

This project aims to build a reproducible, end-to-end data pipeline that uses synthetic industrial telemetry, operating context, and maintenance history to identify equipment at elevated risk of failure.

The pipeline is designed to generate realistic manufacturing data, validate relationships between entities, identify data-quality issues, calculate failure-risk indicators, and produce machine-readable outputs for evaluation.

The project is being developed as part of the YottaFlex AI candidate coding challenge.

## 2. Problem Statement

Manufacturing equipment can develop warning signs before a failure occurs. These signs may include increasing temperature, abnormal vibration, changes in pressure or electrical current, and relevant maintenance history.

The objective is to build a data pipeline that:

- Generates interconnected industrial master and event data.
- Simulates normal operation, shutdowns, sensor faults, and pre-failure patterns.
- Preserves historical maintenance and failure records.
- Validates primary keys, foreign keys, timestamps, ranges, and lifecycle rules.
- Identifies elevated equipment failure risk using documented logic.
- Separates ground-truth labels from prediction inputs.
- Produces evaluation metrics, validation reports, and reproducible datasets.

## 3. Current Implementation Status

The project is being developed incrementally.

### Completed

- Python virtual environment setup.
- Initial project directory structure.
- Configuration file created.
- Initial master-data generator implemented.
- Generation of plants, production lines, machines, and sensors.
- Deterministic ID generation for the starter configuration.
- Basic primary-key and foreign-key validation.
- Initial automated tests for entity counts, relationships, unique IDs, and reproducibility.

### In Progress

- Comprehensive data dictionary and relational schema.
- Operating-shift and telemetry generation.
- Maintenance work orders, technicians, parts, and failure events.
- Pre-failure pattern injection and separate ground-truth labels.
- Required anomaly and exception scenarios.
- Risk scoring, evaluation metrics, and reconciliation reports.
- Full-scale generation and reproducibility verification.

The status above will be updated as each component is implemented and tested.

## 4. Technology Stack

- **Python 3.12:** Pipeline implementation.
- **pandas:** Structured data generation, transformation, and analysis.
- **NumPy:** Numerical operations and synthetic signal generation.
- **pytest:** Automated testing.
- **PostgreSQL:** Planned relational persistence.
- **CSV and JSON:** Portable dataset exports and machine-readable reports.
- **Git and GitHub:** Version control and public source-code hosting.

## 5. Required Dataset Scale

The planned full-scale dataset contains:

| Entity or measurement   |      Target |
| ----------------------- | ----------: |
| Plants                  |           3 |
| Production lines        |          12 |
| Machines                |         100 |
| Sensors                 |         500 |
| Telemetry history       |     90 days |
| Telemetry readings      | 1–3 million |
| Labelled failure events |     100–200 |

The generator will use a fixed random seed, initially `20261022`, and support both a smaller development dataset and a full-scale dataset.

These are target volumes, not a claim that the full dataset has already been generated.

## 6. Core Data Entities

The planned data model includes:

1. `Plant`
2. `ProductionLine`
3. `Machine`
4. `Sensor`
5. `TelemetryEvent`
6. `OperatingShift`
7. `MaintenanceWorkOrder`
8. `FailureEvent`
9. `Part`
10. `Technician`

Primary keys and foreign keys will be used to maintain referential integrity. Bridge tables will represent many-to-many relationships where required.

Entity definitions, field types, units, allowed values, uniqueness rules, and validation requirements will be documented in `docs/data_dictionary.md`.

## 7. Pipeline Workflow

The planned processing workflow is:

1. Load the generation configuration.
2. Generate parent/master entities.
3. Generate dependent operational and maintenance records.
4. Generate timestamped telemetry using machine and sensor context.
5. Inject documented sensor anomalies and pre-failure patterns.
6. Generate ground-truth labels separately from prediction features.
7. Validate schema, identifiers, relationships, timestamps, and business rules.
8. Calculate features and equipment failure-risk scores.
9. Evaluate predictions against ground truth.
10. Export datasets, exception records, validation summaries, and evaluation reports.
11. Repeat generation with the same seed and compare results for reproducibility.

## 8. Required Exception Scenarios

The pipeline is intended to explicitly detect and report:

- Telemetry referencing an unknown sensor.
- Impossible sensor units or measurement ranges.
- Failure timestamps that violate documented symptom-ordering rules.
- Maintenance end timestamps earlier than start timestamps.
- Missing telemetry intervals incorrectly represented as zero-valued measurements.

Exception records will identify the affected record, issue type, expected behavior, and observed behavior wherever applicable.

Sensor faults will be distinguished from actual machine failures.

## 9. Validation and Evaluation

Planned data-quality checks include:

- Primary-key uniqueness.
- Foreign-key integrity.
- Allowed enumeration values.
- Sensor units and measurement ranges.
- Timestamp and lifecycle consistency.
- Duplicate event detection.
- Derived-value and maintenance reconciliation.
- Detection of missing telemetry and explicit anomaly records.
- Reproducibility using fixed-seed generation.

Planned failure-risk evaluation metrics include precision, recall, F1 score, PR-AUC where appropriate, false alarms per machine-day, and failure-warning lead time.

Evaluation will use prediction-time information and separate ground-truth labels to avoid target leakage.

## 10. Installation and Setup

Prerequisites:

- Python 3.12 or a compatible Python version.
- Git.
- A terminal such as PowerShell or the VS Code integrated terminal.

Clone the public repository:

```bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
cd equipment-failure-risk
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the automated tests:

```powershell
python -m pytest tests/ -v
```

The complete pipeline execution command will be documented here once the CLI is implemented.

## 11. Configuration

The pipeline configuration is maintained in `config/config.yaml`.

It will control the random seed, entity counts, telemetry time range, sampling interval, output directories, and sensor specifications.

The starter configuration is intended for rapid development and testing. The full configuration will use the required challenge volumes.

## 12. Reproducibility

Reproducibility is a key acceptance criterion.

The project will:

- Use a fixed random seed.
- Generate stable, deterministic identifiers.
- Derive calculated values from source records.
- Use stable output ordering and serialization where appropriate.
- Compare row counts and file checksums across repeated runs.
- Record configuration and validation results.

The reproducibility report will be added after the full pipeline is implemented.

## 13. Testing Strategy

Automated tests will cover:

- Master-data generation and expected counts.
- Primary-key uniqueness and foreign-key relationships.
- Valid and invalid sensor definitions.
- Telemetry generation and operating-state consistency.
- Maintenance and failure-event lifecycle rules.
- Exception detection.
- Risk-scoring logic.
- Evaluation metrics and label separation.
- Same-seed reproducibility.

Both normal cases and deliberately injected negative scenarios will be tested.

## 14. Assumptions and Limitations

- The initial dataset is synthetic and is not intended to represent any particular real manufacturing plant.
- Simulated failure patterns and risk rules must be documented and evaluated against the corresponding ground truth.
- Performance on synthetic data does not establish real-world predictive accuracy.
- Risk scores are decision-support outputs and do not independently establish that equipment will fail.
- Full-scale generation and evaluation results will be reported only after they have been executed and verified.

## 15. AI-Assisted Development Disclosure

LLM tools are being used to assist with project planning, implementation guidance, code review, testing ideas, and documentation.

The developer is responsible for reviewing generated code, understanding the implementation, running the tests, checking the business rules, and validating the final outputs.

The prompt history and a record of AI assistance, code changes, personal review, and validation will be maintained in `prompts/prompt_history.md` and `docs/ai_usage.md`.

## 16. Project Documentation

- `docs/data_dictionary.md` — Entity definitions and field-level validation rules.
- `docs/business_rules.md` — Business logic, failure patterns, and lifecycle rules.
- `prompts/prompt_history.md` — LLM prompt history.
- `docs/ai_usage.md` — AI assistance and developer validation.
- `config/config.yaml` — Dataset generation configuration.

## 17. License and Data Provenance

The project is intended to use synthetic data generated by its own code. No confidential or personal industrial data is required.

Any future external reference datasets will be documented with their source, version, retrieval date, license, attribution requirements, and transformations before use.

## 18. Author and Submission

Developed for the YottaFlex AI candidate coding challenge.

**Repository:** Add the public GitHub repository URL before submission.

**Submission status:** In development. Final functionality, full-scale validation, and evaluation results will be documented after execution.
