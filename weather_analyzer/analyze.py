"""Analyze hourly wind data to find the calmest hours of the day.

All functions take the DataFrame returned by :func:`weather_analyzer.fetch.fetch_wind`
(indexed by local timestamp, with a ``wind_speed_10m`` column).
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

SPEED = "wind_speed_10m"
GUST = "wind_gusts_10m"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _with_time_parts(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with integer ``hour`` (0-23) and ``month`` (1-12) columns."""
    out = df.copy()
    idx = pd.DatetimeIndex(out.index)
    out["hour"] = idx.hour
    out["month"] = idx.month
    return out


def by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/median wind speed and mean gust per hour of day.

    Returns a DataFrame indexed by hour 0-23 with columns
    ``mean_speed``, ``median_speed``, ``mean_gust``.
    """
    parts = _with_time_parts(df)
    agg = parts.groupby("hour").agg(
        mean_speed=(SPEED, "mean"),
        median_speed=(SPEED, "median"),
        mean_gust=(GUST, "mean"),
    )
    # Ensure all 24 hours are present and ordered.
    return agg.reindex(range(24))


def by_month_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Mean wind speed as a month x hour matrix (rows=month 1-12, cols=hour 0-23)."""
    parts = _with_time_parts(df)
    matrix = parts.pivot_table(
        index="month", columns="hour", values=SPEED, aggfunc="mean"
    )
    return matrix.reindex(index=range(1, 13), columns=range(24))


def calmest_hours(hourly: pd.DataFrame, n: int = 5) -> List[int]:
    """Return the ``n`` calmest hours (lowest mean speed), calmest first."""
    ranked = hourly["mean_speed"].dropna().sort_values()
    return [int(h) for h in ranked.index[:n]]


def calmest_window(hourly: pd.DataFrame, length: int = 3) -> Tuple[int, int, float]:
    """Return the calmest contiguous ``length``-hour window (wrapping midnight).

    Returns (start_hour, end_hour, mean_speed) where the window covers
    start_hour .. end_hour inclusive. Raises ValueError if speeds are unavailable.
    """
    speeds = hourly["mean_speed"]
    if speeds.dropna().empty:
        raise ValueError("No wind-speed data to compute a window from.")
    if not 1 <= length <= 24:
        raise ValueError(f"length must be in 1..24, got {length}.")

    # Work on a full 24-length series; wrap by doubling.
    series = speeds.reindex(range(24))
    doubled = pd.concat([series, series]).reset_index(drop=True)

    best_start, best_mean = 0, float("inf")
    for start in range(24):
        window = doubled.iloc[start:start + length]
        if window.isna().any():
            continue
        m = float(window.mean())
        if m < best_mean:
            best_mean, best_start = m, start
    if best_mean == float("inf"):
        raise ValueError(
            f"No complete {length}-hour window without missing hours was found."
        )
    end = (best_start + length - 1) % 24
    return best_start, end, best_mean


def calmest_hours_by_month(df: pd.DataFrame, n: int = 3) -> "dict[int, List[int]]":
    """Map each month present in the data to its ``n`` calmest hours."""
    parts = _with_time_parts(df)
    result: dict[int, List[int]] = {}
    for month, group in parts.groupby("month"):
        means = group.groupby("hour")[SPEED].mean().sort_values()
        result[int(month)] = [int(h) for h in means.index[:n]]
    return result
