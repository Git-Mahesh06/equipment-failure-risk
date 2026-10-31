
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml

from failure_risk.telemetry_validation import (
    validate_telemetry_file,
)

from failure_risk.pipeline import (
    export_dataset,
    generate_dataset,
    write_dataset_telemetry,
)
from failure_risk.validation_report import create_validation_report
from failure_risk.prediction_pipeline import (
    generate_daily_predictions,
    evaluate_and_save_predictions,
)


def load_config(config_path: Path) -> dict:
    """Load and validate the YAML configuration."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration must contain a YAML mapping.")

    generation = config.get("generation")
    output = config.get("output")

    if not isinstance(generation, dict) or not isinstance(output, dict):
        raise ValueError(
            "Configuration must contain 'generation' and 'output' sections."
        )

    required_generation = [
        "plants",
        "lines",
        "machines",
        "sensors",
        "telemetry_days",
        "telemetry_interval_minutes",
        "target_failures",
    ]

    missing = [
        key for key in required_generation
        if key not in generation
    ]

    if missing:
        raise ValueError(
            f"Missing generation settings: {', '.join(missing)}"
        )

    mode = generation.get("mode", "custom")
    if not isinstance(mode, str) or mode.lower() not in {
        "starter", "full", "custom"
    }:
        raise ValueError(
            "generation.mode must be 'starter', 'full', or 'custom'."
        )

    positive_settings = [
        "plants",
        "lines",
        "machines",
        "sensors",
        "telemetry_days",
        "telemetry_interval_minutes",
    ]

    for key in positive_settings:
        value = generation[key]

        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(
                f"generation.{key} must be a positive integer."
            )

    failures = generation["target_failures"]
    if (
        isinstance(failures, bool)
        or not isinstance(failures, int)
        or not 100 <= failures <= 200
    ):
        raise ValueError(
            "generation.target_failures must be an integer between 100 and 200."
        )

    if "seed" in config and (
        isinstance(config["seed"], bool)
        or not isinstance(config["seed"], int)
    ):
        raise ValueError("seed must be an integer.")

    return config


def run_pipeline(config_path: Path) -> int:
    """Generate, validate, and export the configured dataset."""
    config = load_config(config_path)
    sensor_ranges = load_sensor_ranges(config)

    generation = config["generation"]
    output = config["output"]
    seed = int(config.get("seed", 20261022))

    days = int(generation["telemetry_days"])
    interval_minutes = int(
        generation["telemetry_interval_minutes"]
    )

    if days <= 0 or interval_minutes <= 0:
        raise ValueError(
            "telemetry_days and telemetry_interval_minutes must be positive."
        )

    output_dir = Path(output.get("directory", "data/generated"))
    ground_truth_dir = Path(
        output.get("ground_truth_directory", "data/ground_truth")
    )
    exceptions_dir = Path(
        output.get("exceptions_directory", "data/exceptions")
    )
    report_path = Path("data/reports/validation_report.json")
    telemetry_path = output_dir / "telemetry.csv"
    exceptions_path = exceptions_dir / "telemetry_exceptions.csv"

    print("Starting equipment failure-risk data pipeline...")
    print(f"Configuration: {config_path}")
    print(f"Generation mode: {generation.get('mode', 'custom')}")
    print(f"Random seed: {seed}")

    data = generate_dataset(
        plants_count=int(generation["plants"]),
        lines_count=int(generation["lines"]),
        machines_count=int(generation["machines"]),
        sensors_count=int(generation["sensors"]),
        failures_count=int(generation["target_failures"]),
        start_time="2026-01-01T00:00:00",
        days=days,
        seed=seed,
    )

    print("\nStructured datasets generated.")
    print(f"Machines: {len(data['machines'])}")
    print(f"Sensors: {len(data['sensors'])}")
    print(f"Failure events: {len(data['failure_events'])}")

    report = create_validation_report(
        data,
        output_path=str(report_path),
    )

    print(f"\nValidation status: {report['status']}")
    print(f"Validation report: {report_path}")

    if report["status"] != "passed":
        print("Validation failed. Dataset export has been stopped.")
        for error in report["errors"]:
            print(f"  - {error}")
        return 1

    exported = export_dataset(
        data,
        output_dir=str(output_dir),
        ground_truth_dir=str(ground_truth_dir),
    )

    print("\nStructured datasets exported:")
    for name, path in exported.items():
        print(f"  {name}: {path}")

    telemetry_rows = write_dataset_telemetry(
        data,
        output_path=str(telemetry_path),
        start_time="2026-01-01T00:00:00",
        days=days,
        interval_minutes=interval_minutes,
        seed=seed,
    )

    print(f"\nTelemetry rows written: {telemetry_rows:,}")
    print(f"Telemetry file: {telemetry_path}")

    exception_count = validate_telemetry_file(
        telemetry_path=telemetry_path,
        machines=data["machines"],
        sensors=data["sensors"],
        sensor_ranges=sensor_ranges,
        output_path=exceptions_path,
        chunksize=100_000,
    )

    error_count = 0
    warning_count = 0

    if exceptions_path.exists():
        with exceptions_path.open(
            "r", newline="", encoding="utf-8"
        ) as file:
            for row in csv.DictReader(file):
                severity = row.get("severity", "").strip().upper()

                if severity == "ERROR":
                    error_count += 1
                elif severity == "WARNING":
                    warning_count += 1

    print(f"Telemetry exceptions: {exception_count}")
    print(f"Telemetry errors: {error_count}")
    print(f"Telemetry warnings: {warning_count}")
    print(f"Exception report: {exceptions_path}")
    print(f"Ground truth directory: {ground_truth_dir}")


    if error_count > 0:
        print("Telemetry validation failed. Review the exception report.")
        return 1

    # Generate daily machine failure-risk predictions.
    if days <= 7:
        print(
            "Prediction requires more than 7 days of telemetry "
            "to evaluate the full prediction window."
        )
        return 1

    print("\nGenerating daily machine risk predictions...")

    predictions = generate_daily_predictions(
        telemetry_path=telemetry_path,
        sensors=data["sensors"],
        days=days,
        interval_minutes=interval_minutes,
        start_time="2026-01-01T00:00:00",
        prediction_window_days=7,
    )

    evaluate_and_save_predictions(
        predictions=predictions,
        failure_events=data["failure_events"],
        output_dir=str(report_path.parent),
        prediction_window_days=7,
        risk_threshold=50.0,
    )

    print("\nPipeline completed successfully.")
    return 0


def load_sensor_ranges(config: dict) -> dict[str, dict]:
    """Load sensor operating ranges from the YAML configuration."""
    sensor_config = config.get("sensors", {})

    type_mapping = {
        "temperature": "TEMP",
        "temp": "TEMP",
        "vibration": "VIBRATION",
        "pressure": "PRESSURE",
        "current": "CURRENT",
    }

    sensor_ranges = {}

    for config_name, settings in sensor_config.items():
        if not isinstance(settings, dict):
            raise ValueError(
                f"Sensor configuration '{config_name}' must be a mapping."
            )

        sensor_type = type_mapping.get(config_name.lower())
        if sensor_type is None:
            continue

        for key in ("min_value", "max_value"):
            if key not in settings:
                raise ValueError(
                    f"Sensor configuration '{config_name}' is missing: {key}"
                )

        minimum = float(settings["min_value"])
        maximum = float(settings["max_value"])

        if minimum > maximum:
            raise ValueError(
                f"Invalid physical range for '{config_name}'."
            )

        normal_min = settings.get("normal_min")
        normal_max = settings.get("normal_max")

        if normal_min is not None:
            normal_min = float(normal_min)
        if normal_max is not None:
            normal_max = float(normal_max)

        if (
            normal_min is not None
            and normal_max is not None
            and normal_min > normal_max
        ):
            raise ValueError(
                f"Invalid normal range for '{config_name}'."
            )

        for name, value in (
            ("normal_min", normal_min),
            ("normal_max", normal_max),
        ):
            if value is not None and not minimum <= value <= maximum:
                raise ValueError(
                    f"{name} for '{config_name}' must be within "
                    "the physical range."
                )

        sensor_ranges[sensor_type] = {
            "min_value": minimum,
            "max_value": maximum,
            "normal_min": normal_min,
            "normal_max": normal_max,
        }

    return sensor_ranges



def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate and validate synthetic equipment failure-risk data."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to the YAML configuration file.",
    )

    args = parser.parse_args()

    try:
        return run_pipeline(args.config)
    except Exception as exc:
        print(f"\nPipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
