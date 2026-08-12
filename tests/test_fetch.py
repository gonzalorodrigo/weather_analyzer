"""Unit tests for date-range logic in fetch.py. No network access."""

from __future__ import annotations

import datetime as dt

import pytest

from weather_analyzer import fetch


def test_default_date_range_snaps_to_month_start():
    start, end = fetch.default_date_range(5, today=dt.date(2026, 8, 11))
    # today - 5 days lag = 2026-08-06, snapped to the 1st.
    assert end == "2026-08-01"
    # ~5 years earlier, snapped to the 1st of its month.
    assert start == "2021-08-01"


def test_default_date_range_both_ends_are_first_of_month():
    start, end = fetch.default_date_range(3, today=dt.date(2024, 3, 15))
    assert start.endswith("-01")
    assert end.endswith("-01")


def test_default_date_range_crosses_year_boundary():
    # Early January minus the lag lands in the previous year/month.
    _, end = fetch.default_date_range(1, today=dt.date(2026, 1, 3))
    assert end == "2025-12-01"


def test_default_date_range_rejects_nonpositive_years():
    with pytest.raises(ValueError):
        fetch.default_date_range(0, today=dt.date(2026, 8, 11))
    with pytest.raises(ValueError):
        fetch.default_date_range(-2, today=dt.date(2026, 8, 11))
