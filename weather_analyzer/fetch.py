"""Fetch historical hourly weather data from the Open-Meteo archive (ERA5).

Provides ``fetch_wind`` and ``fetch_solar``, both built on a shared
``_fetch_hourly`` helper. Results are cached to a CSV in the cache dir so
re-runs are instant and don't re-hit the API.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from typing import List, Optional

import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

WIND_VARS = ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]
SOLAR_VARS = ["shortwave_radiation"]

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
    cache_dir: str, prefix: str, lat: float, lon: float, start: str, end: str, tag: str
) -> str:
    fname = f"{prefix}_{lat:.4f}_{lon:.4f}_{start}_{end}_{tag}.csv"
    return os.path.join(cache_dir, fname)


def _read_cache(path: str) -> pd.DataFrame:
    return pd.read_csv(path, index_col="time", parse_dates=["time"])


def _fetch_hourly(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    variables: List[str],
    primary_var: str,
    cache_prefix: str,
    cache_tag: str,
    label: str,
    extra_params: Optional[dict] = None,
    cache_dir: str = "data",
    use_cache: bool = True,
    timeout: float = 60.0,
) -> pd.DataFrame:
    """Fetch (or load from cache) hourly ``variables`` indexed by local time.

    ``primary_var`` is the column NaNs are dropped on; ``label`` is used only in
    status messages. Rows missing the primary variable are dropped.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = _cache_path(
        cache_dir, cache_prefix, latitude, longitude, start_date, end_date, cache_tag
    )
    if use_cache and os.path.exists(path):
        print(f"Using cached {label} data ({os.path.basename(path)}).", file=sys.stderr)
        return _read_cache(path)

    print(
        f"Fetching hourly {label} {start_date} to {end_date} from Open-Meteo...",
        file=sys.stderr,
    )
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(variables),
        "timezone": "auto",
    }
    if extra_params:
        params.update(extra_params)

    resp = requests.get(ARCHIVE_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()

    hourly = payload.get("hourly")
    if not hourly or not hourly.get("time"):
        raise RuntimeError(
            "Open-Meteo returned no hourly data for this location/date range. "
            f"Response keys: {sorted(payload)}."
        )

    df = pd.DataFrame(
        {"time": pd.to_datetime(hourly["time"]), **{v: hourly.get(v) for v in variables}}
    ).set_index("time")

    # Drop rows where the primary signal is missing (occasional NaNs in ERA5).
    df = df.dropna(subset=[primary_var])
    if df.empty:
        raise RuntimeError(f"All {primary_var} values were missing after cleaning.")

    df.to_csv(path, index_label="time")
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
    """Return hourly wind indexed by local timestamp.

    Columns: wind_speed_10m, wind_gusts_10m, wind_direction_10m.
    """
    return _fetch_hourly(
        latitude,
        longitude,
        start_date,
        end_date,
        variables=WIND_VARS,
        primary_var="wind_speed_10m",
        cache_prefix="wind",
        cache_tag=unit,
        label="wind",
        extra_params={"wind_speed_unit": unit},
        cache_dir=cache_dir,
        use_cache=use_cache,
        timeout=timeout,
    )


def fetch_solar(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    cache_dir: str = "data",
    use_cache: bool = True,
    timeout: float = 60.0,
) -> pd.DataFrame:
    """Return hourly shortwave solar radiation (W/m²) indexed by local timestamp.

    Column: shortwave_radiation.
    """
    return _fetch_hourly(
        latitude,
        longitude,
        start_date,
        end_date,
        variables=SOLAR_VARS,
        primary_var="shortwave_radiation",
        cache_prefix="solar",
        cache_tag="rad",
        label="solar radiation",
        cache_dir=cache_dir,
        use_cache=use_cache,
        timeout=timeout,
    )
