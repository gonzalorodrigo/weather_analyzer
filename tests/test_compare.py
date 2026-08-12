"""Unit tests for the wind-vs-sun comparison logic. No network access."""

from __future__ import annotations

import numpy as np
import pandas as pd

from weather_analyzer import report, solar


def _wind_hourly(min_hour: int = 9) -> pd.DataFrame:
    """Mean wind by hour, lowest at ``min_hour`` (triangular profile)."""
    hours = np.arange(24)
    speed = 5 + np.abs(hours - min_hour)
    return pd.DataFrame({"mean_speed": speed}, index=pd.Index(hours, name="hour"))


def _sun_hourly() -> pd.DataFrame:
    """Mean radiation by hour: daylight 07-17, peak at noon, night = 0."""
    hours = np.arange(24)
    frac = np.clip((hours - 6) / 12.0, 0.0, 1.0)
    rad = np.where((hours > 6) & (hours < 18), 700.0 * np.sin(np.pi * frac), 0.0)
    return pd.DataFrame({"mean_radiation": rad}, index=pd.Index(hours, name="hour"))


def test_combined_only_returns_daylight_hours():
    wind, sun = _wind_hourly(), _sun_hourly()
    daylight = set(solar.daylight_hours(sun))
    best = report.combined_watering_hours(wind, sun, n=3)
    assert len(best) == 3
    assert set(best) <= daylight  # never a night hour
    assert 0 not in best


def test_combined_excludes_windiest_and_sunniest():
    wind, sun = _wind_hourly(min_hour=9), _sun_hourly()
    best = report.combined_watering_hours(wind, sun, n=3)
    # Noon is the sunniest hour; hour 23 is the windiest — neither should win.
    assert 12 not in best
    assert 23 not in best


def test_combined_empty_without_daylight():
    wind = _wind_hourly()
    dark = pd.DataFrame(
        {"mean_radiation": np.zeros(24)}, index=pd.Index(np.arange(24), name="hour")
    )
    assert report.combined_watering_hours(wind, dark, n=3) == []


def test_compare_table_lists_all_hours_and_both_columns():
    wind, sun = _wind_hourly(), _sun_hourly()
    daylight = set(solar.daylight_hours(sun))
    table = report.compare_table(wind, sun, "kmh", daylight)
    assert "wind km/h" in table
    assert "sun W/m²" in table
    # 2 header lines + 24 hour rows.
    assert len(table.splitlines()) == 26
    assert "00:00" in table and "23:00" in table
