"""Fetch historical hourly wind data from the Open-Meteo archive (ERA5).

Results are cached to a CSV in the cache dir so re-runs are instant and don't
re-hit the API.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from typing import Optional

import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARS = ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]

# ERA5 reanalysis lags real time by a few days; stay behind the edge so the
# most recent requested days actually have data.
_ARCHIVE_LAG_DAYS = 5


def default_date_range(years: int, today: Optional[dt.date] = None) -> tuple[str, str]:
    """Return (start_date, end_date) ISO strings spanning ``years`` back.

    The end date is held a few days behind today for the archive lag, then both
    ends are snapped to the first of the month. Snapping keeps the date range —
    and therefore the cache key — stable across re-runs within the same month,
    so you only download once per month instead of once per day.
    """
    if years <= 0:
        raise ValueError(f"years must be positive, got {years}.")
    if today is None:
        today = dt.date.today()
    lagged = today - dt.timedelta(days=_ARCHIVE_LAG_DAYS)
    # Snap to the first of the month (stable cache key within a month).
    end = lagged.replace(day=1)
    # Approximate a calendar-year span, then snap start to its month too.
    start = (end - dt.timedelta(days=365 * years)).replace(day=1)
    return start.isoformat(), end.isoformat()


def _cache_path(
    cache_dir: str, lat: float, lon: float, start: str, end: str, unit: str
) -> str:
    fname = f"wind_{lat:.4f}_{lon:.4f}_{start}_{end}_{unit}.csv"
    return os.path.join(cache_dir, fname)


def _read_cache(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col="time", parse_dates=["time"])
    return df


def fetch_wind(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    unit: str = "kmh",
    cache_dir: str = "data",
    use_cache: bool = True,
    timeout: float = 60.0,
) -> pd.DataFrame:
    """Return a DataFrame of hourly wind indexed by local timestamp.

    Columns: wind_speed_10m, wind_gusts_10m, wind_direction_10m. Uses a CSV
    cache in ``cache_dir`` keyed by location/date-range/unit.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = _cache_path(cache_dir, latitude, longitude, start_date, end_date, unit)
    if use_cache and os.path.exists(path):
        print(f"Using cached wind data ({os.path.basename(path)}).", file=sys.stderr)
        return _read_cache(path)

    print(
        f"Fetching hourly wind {start_date} to {end_date} (unit: {unit}) from Open-Meteo...",
        file=sys.stderr,
    )
    resp = requests.get(
        ARCHIVE_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(HOURLY_VARS),
            "wind_speed_unit": unit,
            "timezone": "auto",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()

    hourly = payload.get("hourly")
    if not hourly or not hourly.get("time"):
        raise RuntimeError(
            "Open-Meteo returned no hourly data for this location/date range. "
            f"Response keys: {sorted(payload)}."
        )

    df = pd.DataFrame(
        {"time": pd.to_datetime(hourly["time"]), **{v: hourly.get(v) for v in HOURLY_VARS}}
    ).set_index("time")

    # Drop rows where the primary signal is missing (occasional NaNs in ERA5).
    df = df.dropna(subset=["wind_speed_10m"])
    if df.empty:
        raise RuntimeError("All wind_speed_10m values were missing after cleaning.")

    df.to_csv(path, index_label="time")
    return df
