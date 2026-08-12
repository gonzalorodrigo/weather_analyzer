"""Analyze hourly solar radiation to find the least-sun *daylight* hours.

Nighttime radiation is ~0, so a naive "least sun" ranking is just "night". These
helpers filter to daylight (hours whose mean radiation exceeds a small
threshold) and rank within it, surfacing the weak-sun edges around dawn/dusk.

Input is the DataFrame from :func:`weather_analyzer.fetch.fetch_solar` (indexed
by local timestamp, with a ``shortwave_radiation`` column).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

# Reuse the shared hour/month helper rather than duplicating it.
from .analyze import MONTH_NAMES, _with_time_parts

RADIATION = "shortwave_radiation"

# An hour of day counts as "daylight" when its mean irradiance exceeds this
# (W/m²). Small enough to include dawn/dusk, large enough to exclude true night.
DEFAULT_DAYLIGHT_THRESHOLD = 5.0


def by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/median solar radiation per hour of day.

    Returns a DataFrame indexed by hour 0-23 with columns
    ``mean_radiation`` and ``median_radiation``.
    """
    parts = _with_time_parts(df)
    agg = parts.groupby("hour").agg(
        mean_radiation=(RADIATION, "mean"),
        median_radiation=(RADIATION, "median"),
    )
    return agg.reindex(range(24))


def by_month_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Mean radiation as a month x hour matrix (rows=month 1-12, cols=hour 0-23)."""
    parts = _with_time_parts(df)
    matrix = parts.pivot_table(
        index="month", columns="hour", values=RADIATION, aggfunc="mean"
    )
    return matrix.reindex(index=range(1, 13), columns=range(24))


def daylight_hours(
    hourly: pd.DataFrame, threshold: float = DEFAULT_DAYLIGHT_THRESHOLD
) -> List[int]:
    """Hours of day whose mean radiation exceeds ``threshold`` (sun is up)."""
    means = hourly["mean_radiation"]
    return [int(h) for h in means.index[means > threshold]]


def least_sun_daylight_hours(
    hourly: pd.DataFrame,
    n: int = 5,
    threshold: float = DEFAULT_DAYLIGHT_THRESHOLD,
) -> List[int]:
    """The ``n`` daylight hours with the least sun, weakest first.

    Night is excluded by the daylight filter, so this never returns 3am.
    """
    means = hourly["mean_radiation"].dropna()
    daylight = means[means > threshold].sort_values()
    return [int(h) for h in daylight.index[:n]]


def daylight_span(
    hourly: pd.DataFrame, threshold: float = DEFAULT_DAYLIGHT_THRESHOLD
) -> Tuple[int, int, int]:
    """Return (first_daylight_hour, last_daylight_hour, peak_hour).

    Raises ValueError if no hour clears the daylight threshold (e.g. polar night).
    """
    hours = daylight_hours(hourly, threshold)
    if not hours:
        raise ValueError(
            f"No daylight hours above {threshold} W/m² were found."
        )
    peak = int(hourly["mean_radiation"].idxmax())
    return min(hours), max(hours), peak


def least_sun_daylight_by_month(
    df: pd.DataFrame,
    n: int = 3,
    threshold: float = DEFAULT_DAYLIGHT_THRESHOLD,
) -> Dict[int, List[int]]:
    """Map each month present in the data to its ``n`` least-sun daylight hours."""
    parts = _with_time_parts(df)
    result: Dict[int, List[int]] = {}
    for month, group in parts.groupby("month"):
        means = group.groupby("hour")[RADIATION].mean()
        daylight = means[means > threshold].sort_values()
        result[int(month)] = [int(h) for h in daylight.index[:n]]
    return result
