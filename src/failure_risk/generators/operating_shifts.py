
import pandas as pd


SHIFT_DEFINITIONS = [
    {
        "shift_name": "MORNING",
        "start_hour": 6,
        "end_hour": 14,
    },
    {
        "shift_name": "EVENING",
        "start_hour": 14,
        "end_hour": 22,
    },
    {
        "shift_name": "NIGHT",
        "start_hour": 22,
        "end_hour": 6,
    },
]


def generate_operating_shifts(
    machines: pd.DataFrame,
    start_time: str = "2026-01-01T00:00:00",
    days: int = 90,
) -> pd.DataFrame:
    """
    Generate deterministic operating-shift records for each machine.

    Each machine receives three shifts per day:
    MORNING: 06:00-14:00
    EVENING: 14:00-22:00
    NIGHT:   22:00-06:00 the following day

    Night shifts may end after the observation window.
    """

    if machines.empty:
        raise ValueError("machines must not be empty")

    if "machine_id" not in machines.columns:
        raise ValueError("machines must contain a machine_id column")

    if machines["machine_id"].isna().any():
        raise ValueError("machine_id must not contain null values")

    if machines["machine_id"].duplicated().any():
        raise ValueError("machine_id values must be unique")

    if days <= 0:
        raise ValueError("days must be greater than zero")

    start = pd.Timestamp(start_time)

    if pd.isna(start):
        raise ValueError("start_time must be a valid timestamp")

    if start.tz is not None:
        raise ValueError("start_time must be timezone-naive")

    # Generate calendar-aligned shifts beginning on the start date.
    first_day = start.normalize()
    records = []
    shift_counter = 1

    for machine_id in machines["machine_id"]:
        for day_offset in range(days):
            shift_date = first_day + pd.Timedelta(days=day_offset)

            for definition in SHIFT_DEFINITIONS:
                shift_start = shift_date + pd.Timedelta(
                    hours=definition["start_hour"]
                )

                shift_end = shift_date + pd.Timedelta(
                    hours=definition["end_hour"]
                )

                # Night shift ends on the following calendar day.
                if definition["end_hour"] <= definition["start_hour"]:
                    shift_end += pd.Timedelta(days=1)

                records.append(
                    {
                        "shift_id": f"SHIFT-{shift_counter:07d}",
                        "machine_id": machine_id,
                        "shift_name": definition["shift_name"],
                        "shift_start": shift_start,
                        "shift_end": shift_end,
                    }
                )

                shift_counter += 1

    result = pd.DataFrame(records)

    # Keep only shifts that overlap the requested observation window.
    window_end = start + pd.Timedelta(days=days)
    result = result[
        (result["shift_end"] > start)
        & (result["shift_start"] < window_end)
    ].copy()

    result = result.reset_index(drop=True)
    return result
