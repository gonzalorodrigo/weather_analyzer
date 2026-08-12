"""Unit tests for the analysis functions. No network access.

We synthesize hourly data with a deliberately calm window (03:00-05:00) and a
windy afternoon, then assert the analysis surfaces it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from weather_analyzer import analyze


def _synthetic_frame() -> pd.DataFrame:
    """Two years of hourly data with a fixed diurnal wind profile.

    Speed is lowest at hour 4 and peaks mid-afternoon, plus a small
    deterministic month wobble so per-month grouping has signal.
    """
    index = pd.date_range("2022-01-01", "2023-12-31 23:00", freq="H")
    hours = index.hour.to_numpy()
    months = index.month.to_numpy()
    # Cosine profile: minimum at hour 4, maximum ~hour 16.
    base = 10 + 6 * np.cos((hours - 16) / 24 * 2 * np.pi)
    speed = base + 0.5 * np.sin(months / 12 * 2 * np.pi)
    gust = speed * 1.6
    return pd.DataFrame(
        {"wind_speed_10m": speed, "wind_gusts_10m": gust, "wind_direction_10m": 180.0},
        index=index,
    )


@pytest.fixture
def frame() -> pd.DataFrame:
    return _synthetic_frame()


def test_by_hour_has_all_24_hours(frame):
    hourly = analyze.by_hour(frame)
    assert list(hourly.index) == list(range(24))
    assert hourly["mean_speed"].notna().all()


def test_calmest_hour_is_around_4am(frame):
    hourly = analyze.by_hour(frame)
    calm = analyze.calmest_hours(hourly, n=3)
    # The synthetic minimum is at hour 4; it must be the calmest.
    assert calm[0] == 4
    assert set(calm) <= {2, 3, 4, 5, 6}


def test_calmest_window_brackets_the_minimum(frame):
    hourly = analyze.by_hour(frame)
    start, end, mean_speed = analyze.calmest_window(hourly, length=3)
    hours = {(start + i) % 24 for i in range(3)}
    assert 4 in hours
    assert mean_speed < hourly["mean_speed"].mean()


def test_by_month_hour_matrix_shape(frame):
    matrix = analyze.by_month_hour(frame)
    assert matrix.shape == (12, 24)
    assert list(matrix.index) == list(range(1, 13))
    assert list(matrix.columns) == list(range(24))


def test_calmest_hours_by_month_covers_present_months(frame):
    by_month = analyze.calmest_hours_by_month(frame, n=3)
    assert set(by_month) == set(range(1, 13))
    for hours in by_month.values():
        assert len(hours) == 3
        assert all(0 <= h <= 23 for h in hours)


def test_calmest_window_rejects_bad_length(frame):
    hourly = analyze.by_hour(frame)
    with pytest.raises(ValueError):
        analyze.calmest_window(hourly, length=0)


def test_calmest_window_wraps_midnight():
    # Diurnal profile with its minimum at hour 23, so the calmest window
    # straddles midnight and exercises the wrap-around (doubling) logic.
    index = pd.date_range("2022-01-01", "2022-12-31 23:00", freq="H")
    hours = index.hour.to_numpy()
    speed = 10 - 6 * np.cos((hours - 23) / 24 * 2 * np.pi)
    df = pd.DataFrame(
        {"wind_speed_10m": speed, "wind_gusts_10m": speed * 1.5, "wind_direction_10m": 90.0},
        index=index,
    )
    hourly = analyze.by_hour(df)
    start, end, _ = analyze.calmest_window(hourly, length=3)
    hours_in_window = {(start + i) % 24 for i in range(3)}
    assert 23 in hours_in_window
    assert start > end  # window wraps past midnight, e.g. 22:00 -> 00:00


def test_calmest_window_raises_when_every_window_has_nan(frame):
    hourly = analyze.by_hour(frame)
    # NaN out every 3rd hour: any 3 consecutive hours then contain a NaN,
    # so no complete length-3 window exists.
    hourly = hourly.copy()
    hourly.loc[[0, 3, 6, 9, 12, 15, 18, 21], "mean_speed"] = np.nan
    with pytest.raises(ValueError):
        analyze.calmest_window(hourly, length=3)
