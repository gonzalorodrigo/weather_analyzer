"""Unit tests for the year-overview suitability logic. No network access."""

from __future__ import annotations

import numpy as np
import pandas as pd

from weather_analyzer import report, solar


def _matrices():
    """Build month x hour wind and sun matrices with a known best cell.

    Sun: daylight 07-17 (sine bump, night = 0). Wind: lowest at hour 9.
    The best (lowest-score) daylight cell should sit in the early morning where
    both wind and sun are low — never at night or midday.
    """
    months = range(1, 13)
    hours = np.arange(24)
    frac = np.clip((hours - 6) / 12.0, 0.0, 1.0)
    sun_row = np.where((hours > 6) & (hours < 18), 700.0 * np.sin(np.pi * frac), 0.0)
    wind_row = 5 + np.abs(hours - 9)

    wind = pd.DataFrame(
        {h: [wind_row[h]] * 12 for h in hours}, index=list(months)
    )
    sun = pd.DataFrame({h: [sun_row[h]] * 12 for h in hours}, index=list(months))
    wind.columns.name = "hour"
    sun.columns.name = "hour"
    return wind, sun


def test_suitability_masks_night_cells():
    wind, sun = _matrices()
    score = report.suitability_matrix(wind, sun)
    assert score.shape == (12, 24)
    # Night hours (0 sun) are below the daylight threshold -> NaN.
    assert score[0].isna().all()
    assert score[3].isna().all()
    # Daylight hours have finite scores.
    assert score[9].notna().all()


def test_best_hour_per_month_is_daylight_and_not_extreme():
    wind, sun = _matrices()
    score = report.suitability_matrix(wind, sun)
    best = report.best_hour_per_month(score)
    assert set(best) == set(range(1, 13))
    for hour in best.values():
        assert 7 <= hour <= 17  # daylight only
        assert hour != 12  # noon is sunniest -> never best


def test_normalize_frame_handles_flat_and_nan():
    flat = pd.DataFrame({0: [5.0, 5.0], 1: [5.0, 5.0]})
    out = report._normalize_frame(flat)
    assert (out.values == 0).all()

    with_nan = pd.DataFrame({0: [0.0, np.nan], 1: [10.0, 5.0]})
    norm = report._normalize_frame(with_nan)
    assert norm.iloc[0, 0] == 0.0  # global min -> 0
    assert norm.iloc[0, 1] == 1.0  # global max -> 1
    assert pd.isna(norm.iloc[1, 0])  # NaN stays NaN


def test_best_hour_per_month_empty_without_daylight():
    wind, _ = _matrices()
    dark = pd.DataFrame(
        {h: [0.0] * 12 for h in range(24)}, index=list(range(1, 13))
    )
    score = report.suitability_matrix(wind, dark)
    assert report.best_hour_per_month(score) == {}
