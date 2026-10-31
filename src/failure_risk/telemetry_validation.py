
from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "telemetry_id",
    "machine_id",
    "sensor_id",
    "timestamp",
    "value",
}



def validate_telemetry(
    telemetry: pd.DataFrame,
    machines: pd.DataFrame | None = None,
    sensors: pd.DataFrame | None = None,
    sensor_ranges: dict[str, dict] | None = None,
) -> list[dict]:
    """Validate telemetry records and return machine-readable exceptions."""
    exceptions: list[dict] = []

    def add_exception(
        exception_type: str,
        severity: str,
        index=None,
        column=None,
        message: str = "",
        **extra,
    ) -> None:
        """Add an exception with consistent diagnostic fields."""
        record = {
            "exception_type": exception_type,
            "severity": severity,
            "row_index": str(index) if index is not None else None,
            "machine_id": None,
            "sensor_id": None,
            "sensor_type": None,
            "timestamp": None,
            "column": column,
            "reading_value": None,
            "normal_min": None,
            "normal_max": None,
            "message": message,
        }

        if index is not None and index in telemetry.index:
            for field in ("machine_id", "sensor_id", "timestamp"):
                if field in telemetry.columns:
                    value = telemetry.at[index, field]
                    record[field] = (
                        None if pd.isna(value) else str(value)
                    )

            if "value" in telemetry.columns:
                value = pd.to_numeric(
                    pd.Series([telemetry.at[index, "value"]]),
                    errors="coerce",
                ).iloc[0]

                if pd.notna(value):
                    record["reading_value"] = float(value)

        record.update(extra)
        exceptions.append(record)

    # 1. Required columns
    missing_columns = REQUIRED_COLUMNS - set(telemetry.columns)

    if missing_columns:
        add_exception(
            "MISSING_COLUMNS",
            "ERROR",
            message=f"Missing required columns: {sorted(missing_columns)}",
        )
        return exceptions

    if telemetry.empty:
        add_exception(
            "EMPTY_TELEMETRY",
            "ERROR",
            message="Telemetry dataset contains no records.",
        )
        return exceptions

    # 2. Missing required values
    for column in [
        "telemetry_id",
        "machine_id",
        "sensor_id",
        "timestamp",
    ]:
        for index in telemetry.index[telemetry[column].isna()]:
            add_exception(
                "NULL_REQUIRED_VALUE",
                "ERROR",
                index,
                column,
                f"{column} is missing.",
            )

    # 3. Duplicate telemetry IDs
    duplicate_mask = telemetry["telemetry_id"].duplicated(
        keep=False
    )

    for index in telemetry.index[duplicate_mask]:
        add_exception(
            "DUPLICATE_TELEMETRY_ID",
            "ERROR",
            index,
            "telemetry_id",
            "Telemetry ID is duplicated.",
        )

    # 4. Numeric readings
    numeric_values = pd.to_numeric(
        telemetry["value"],
        errors="coerce",
    )

    for index in telemetry.index[numeric_values.isna()]:
        add_exception(
            "INVALID_READING",
            "ERROR",
            index,
            "value",
            "Telemetry reading is not numeric.",
        )

    # 5. Timestamps
    invalid_timestamp = pd.to_datetime(
        telemetry["timestamp"],
        errors="coerce",
    ).isna()

    for index in telemetry.index[invalid_timestamp]:
        add_exception(
            "INVALID_TIMESTAMP",
            "ERROR",
            index,
            "timestamp",
            "Telemetry timestamp is invalid.",
        )

    # 6. Known machines
    if machines is not None and "machine_id" in machines.columns:
        known_machines = set(machines["machine_id"].dropna())
        invalid_machines = ~telemetry["machine_id"].isin(
            known_machines
        )

        for index in telemetry.index[invalid_machines]:
            add_exception(
                "UNKNOWN_MACHINE",
                "ERROR",
                index,
                "machine_id",
                "Telemetry references an unknown machine.",
            )

    # 7. Known sensors and machine-sensor relationships
    sensor_lookup = None
    sensor_types = None

    if sensors is not None and {
        "sensor_id",
        "machine_id",
    }.issubset(sensors.columns):
        sensor_lookup = (
            sensors.dropna(subset=["sensor_id"])
            .drop_duplicates("sensor_id", keep="first")
            .set_index("sensor_id")["machine_id"]
        )

        known_sensor_ids = set(sensor_lookup.index)
        unknown_sensors = ~telemetry["sensor_id"].isin(
            known_sensor_ids
        )

        for index in telemetry.index[unknown_sensors]:
            add_exception(
                "UNKNOWN_SENSOR",
                "ERROR",
                index,
                "sensor_id",
                "Telemetry references an unknown sensor.",
            )

        valid_sensor_rows = telemetry[
            telemetry["sensor_id"].isin(known_sensor_ids)
        ]

        expected_machines = valid_sensor_rows["sensor_id"].map(
            sensor_lookup
        )

        mismatched = (
            expected_machines.notna()
            & (
                expected_machines
                != valid_sensor_rows["machine_id"]
            )
        )

        for index in valid_sensor_rows.index[mismatched]:
            add_exception(
                "SENSOR_MACHINE_MISMATCH",
                "ERROR",
                index,
                "machine_id",
                "Sensor does not belong to the referenced machine.",
            )

    # 8. Physical and normal sensor operating ranges
    if (
        sensor_ranges
        and sensors is not None
        and {"sensor_id", "sensor_type"}.issubset(sensors.columns)
    ):
        sensor_types = (
            sensors.dropna(subset=["sensor_id"])
            .drop_duplicates("sensor_id", keep="first")
            .set_index("sensor_id")["sensor_type"]
        )

        telemetry_sensor_types = telemetry["sensor_id"].map(
            sensor_types
        )

        for index in telemetry.index:
            value = numeric_values.loc[index]

            if pd.isna(value):
                continue

            # Scheduled shutdown readings are intentionally zero.
            # Do not flag them as abnormal operating readings.
            if (
                "operating_state" in telemetry.columns
                and telemetry.at[index, "operating_state"] == "STOPPED"
            ):
                continue

            sensor_type = telemetry_sensor_types.loc[index]

            if pd.isna(sensor_type):
                continue

            limits = sensor_ranges.get(sensor_type)

            if not limits:
                continue

            minimum = limits.get("min_value")
            maximum = limits.get("max_value")
            normal_min = limits.get("normal_min")
            normal_max = limits.get("normal_max")

            outside_physical_range = (
                (minimum is not None and value < minimum)
                or (maximum is not None and value > maximum)
            )

            if outside_physical_range:
                add_exception(
                    "OUT_OF_RANGE",
                    "ERROR",
                    index,
                    "value",
                    (
                        f"Reading {value} is outside the physical "
                        f"range [{minimum}, {maximum}] for "
                        f"sensor type {sensor_type}."
                    ),
                    sensor_type=str(sensor_type),
                    normal_min=normal_min,
                    normal_max=normal_max,
                )

            elif (
                (normal_min is not None and value < normal_min)
                or (normal_max is not None and value > normal_max)
            ):
                add_exception(
                    "ABNORMAL_READING",
                    "WARNING",
                    index,
                    "value",
                    (
                        f"Reading {value} is outside the normal "
                        f"range [{normal_min}, {normal_max}] for "
                        f"sensor type {sensor_type}."
                    ),
                    sensor_type=str(sensor_type),
                    normal_min=normal_min,
                    normal_max=normal_max,
                )

    return exceptions



def write_exception_report(
    exceptions: list[dict],
    output_path: str | Path = "data/exceptions/telemetry_exceptions.csv",
) -> Path:
    """Write validation exceptions to CSV, including an empty report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "exception_type",
        "severity",
        "row_index",
        "machine_id",
        "sensor_id",
        "sensor_type",
        "timestamp",
        "column",
        "reading_value",
        "normal_min",
        "normal_max",
        "message",
    ]

    pd.DataFrame(exceptions).reindex(columns=columns).to_csv(
        destination,
        index=False,
    )

    return destination



def validate_telemetry_file(
    telemetry_path: str | Path,
    machines: pd.DataFrame | None = None,
    sensors: pd.DataFrame | None = None,
    sensor_ranges: dict[str, dict] | None = None,
    output_path: str | Path = "data/exceptions/telemetry_exceptions.csv",
    chunksize: int = 100_000,
) -> int:
    """Validate a telemetry CSV in chunks and write exceptions incrementally."""
    source = Path(telemetry_path)
    destination = Path(output_path)

    if chunksize <= 0:
        raise ValueError("chunksize must be positive.")

    if not source.is_file():
        raise FileNotFoundError(
            f"Telemetry file not found: {source}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    total_exceptions = 0
    first_chunk = True

    try:
        for chunk in pd.read_csv(source, chunksize=chunksize):
            exceptions = validate_telemetry(
                chunk,
                machines=machines,
                sensors=sensors,
                sensor_ranges=sensor_ranges,
            )

            if exceptions:

                exception_df = pd.DataFrame(exceptions).reindex(
                    columns=[
                        "exception_type",
                        "severity",
                        "row_index",
                        "machine_id",
                        "sensor_id",
                        "sensor_type",
                        "timestamp",
                        "column",
                        "reading_value",
                        "normal_min",
                        "normal_max",
                        "message",
                    ]
                )


                exception_df.to_csv(
                    destination,
                    mode="w" if first_chunk else "a",
                    header=first_chunk,
                    index=False,
                )

                first_chunk = False
                total_exceptions += len(exceptions)

    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"Telemetry CSV is empty or has no readable header: {source}"
        ) from exc

    if first_chunk:
        write_exception_report([], destination)

    return total_exceptions
