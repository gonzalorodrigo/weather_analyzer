"""Unit tests for the solar-radiation analysis. No network access.

Synthesizes a clean day/night radiation profile: zero at night, a sine bump
peaking at noon, with weak sun at the daylight edges (07:00 and 17:00).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from weather_analyzer import solar


def _synthetic_frame() -> pd.DataFrame:
    """Two years of hourly radiation: daylight 07:00-17:00, night = 0."""
    index = pd.date_range("2022-01-01", "2023-12-31 23:00", freq="H")
    hours = index.hour.to_numpy()
    # sin bump over 06..18; exactly 0 at 06 and 18, small at 07 and 17.
    frac = np.clip((hours - 6) / 12.0, 0.0, 1.0)
    radiation = np.where((hours > 6) & (hours < 18), 700.0 * np.sin(np.pi * frac), 0.0)
    return pd.DataFrame({"shortwave_radiation": radiation}, index=index)


@pytest.fixture
def frame() -> pd.DataFrame:
    return _synthetic_frame()


def test_by_hour_has_all_24_hours(frame):
    hourly = solar.by_hour(frame)
    assert list(hourly.index) == list(range(24))
    assert (hourly["mean_radiation"].fillna(0) >= 0).all()


def test_daylight_excludes_night(frame):
    hourly = solar.by_hour(frame)
    daylight = set(solar.daylight_hours(hourly))
    # 07:00-17:00 are lit; 06 and 18 are exactly 0 (excluded), as is all night.
    assert daylight == set(range(7, 18))
    assert 0 not in daylight
    assert 3 not in daylight


def test_least_sun_daylight_hours_are_the_edges_not_night(frame):
    hourly = solar.by_hour(frame)
    weak = solar.least_sun_daylight_hours(hourly, n=2)
    # Weakest daylight sun is at the dawn/dusk edges, symmetric here.
    assert set(weak) == {7, 17}
    # Crucially, never a night hour despite night having the global minimum (0).
    assert 0 not in weak


def test_daylight_span(frame):
    hourly = solar.by_hour(frame)
    first, last, peak = solar.daylight_span(hourly)
    assert first == 7
    assert last == 17
    assert peak == 12  # sine bump peaks at local noon


def test_by_month_hour_matrix_shape(frame):
    matrix = solar.by_month_hour(frame)
    assert matrix.shape == (12, 24)
    assert list(matrix.index) == list(range(1, 13))
    assert list(matrix.columns) == list(range(24))


def test_least_sun_by_month_returns_daylight_hours(frame):
    by_month = solar.least_sun_daylight_by_month(frame, n=3)
    assert set(by_month) == set(range(1, 13))
    for hours in by_month.values():
        assert all(7 <= h <= 17 for h in hours)


def test_daylight_span_raises_without_daylight():
    # All-night (zero radiation) frame -> no daylight hours.
    index = pd.date_range("2022-01-01", "2022-01-31 23:00", freq="H")
    dark = pd.DataFrame({"shortwave_radiation": 0.0}, index=index)
    hourly = solar.by_hour(dark)
    assert solar.daylight_hours(hourly) == []
    with pytest.raises(ValueError):
        solar.daylight_span(hourly)
