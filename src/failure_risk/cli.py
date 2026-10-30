
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from failure_risk.pipeline import (
    export_dataset,
    generate_dataset,
    write_dataset_telemetry,
)
from failure_risk.validation_report import create_validation_report


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

    return config


def run_pipeline(config_path: Path) -> int:
    """Generate, validate, and export the configured dataset."""
    config = load_config(config_path)

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
    report_path = Path("data/reports/validation_report.json")
    telemetry_path = output_dir / "telemetry.csv"

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
    print(f"Ground truth directory: {ground_truth_dir}")
    print("\nPipeline completed successfully.")

    return 0


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
