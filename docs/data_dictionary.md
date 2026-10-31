# Data Dictionary

## Overview

The Equipment Failure Risk Prediction Pipeline generates synthetic industrial
master data, telemetry readings, failure events, and related maintenance data.

The project uses CSV files for generated datasets and keeps failure ground
truth separate from ordinary input data.

## Master Data

| Dataset          | Description                               | Key fields                               |
| ---------------- | ----------------------------------------- | ---------------------------------------- |
| plants           | Industrial plants                         | plant_id                                 |
| production_lines | Production lines associated with plants   | line_id, plant_id                        |
| machines         | Machines associated with production lines | machine_id, line_id                      |
| sensors          | Sensors assigned to machines              | sensor_id, machine_id, sensor_type, unit |
| technicians      | Maintenance technicians                   | technician_id                            |
| operating_shifts | Operating shift definitions               | Shift identifier and shift attributes    |
| parts            | Maintenance parts inventory               | Part identifier and part attributes      |

## Operational Data

| Dataset                 | Description                                                | Key fields                                                                                   |
| ----------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| failure_events          | Simulated machine failure events; retained as ground truth | machine_id, failure_timestamp, failure_type                                                  |
| maintenance_work_orders | Simulated maintenance activities                           | Work-order identifier and related entity references                                          |
| parts_usage             | Parts associated with maintenance activities               | Part and work-order references                                                               |
| telemetry               | Time-series sensor measurements                            | telemetry_id, sensor_id, machine_id, timestamp, value, unit, operating_state, quality_status |

Exact column names should be verified against the generated CSV headers.

## Telemetry Fields

| Field           | Meaning                                             |
| --------------- | --------------------------------------------------- |
| telemetry_id    | Unique identifier for a telemetry reading           |
| sensor_id       | Identifier of the sensor producing the reading      |
| machine_id      | Machine associated with the sensor                  |
| timestamp       | Time at which the reading is recorded               |
| operating_state | Simulated machine state, such as RUNNING or STOPPED |
| value           | Numeric sensor measurement                          |
| unit            | Measurement unit                                    |
| quality_status  | Simulated reading status, such as GOOD or SHUTDOWN  |

## Sensor Types and Units

| Sensor type | Unit |
| ----------- | ---- |
| TEMP        | degC |
| VIBRATION   | mm/s |
| PRESSURE    | kPa  |
| CURRENT     | A    |

## Prediction Outputs

The risk prediction output contains machine-level risk predictions. The evaluation
output reports prediction metrics against failure-event ground truth.

Expected output files include:

- `data/reports/risk_predictions.csv`
- `data/reports/risk_evaluation.json`

The exact prediction columns and evaluation JSON schema should be confirmed
from the generated files.

## Data Design Notes

- The data is synthetic and is not collected from real industrial equipment.
- Identifiers and relationships are validated by the project.
- Failure events are ground truth and should not be treated as ordinary
  predictive input features.
- Sensor units and value ranges are defined by the telemetry generator and
  project configuration.
