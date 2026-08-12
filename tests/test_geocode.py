"""Unit tests for location parsing in geocode.py.

All cases here use the "lat, lon" fast path or input validation, so none touch
the network (place-name geocoding, which does, is not exercised).
"""

from __future__ import annotations

import pytest

from weather_analyzer.geocode import Location, _parse_latlon, geocode


def test_parse_latlon_valid():
    loc = _parse_latlon("40.015, -105.27")
    assert isinstance(loc, Location)
    assert loc.latitude == pytest.approx(40.015)
    assert loc.longitude == pytest.approx(-105.27)


def test_parse_latlon_tolerates_whitespace_and_space_separator():
    assert _parse_latlon("  40 -105 ") == Location(40.0, -105.0, "40.0000, -105.0000")


def test_parse_latlon_returns_none_for_place_names():
    # A comma-containing place name must fall through to geocoding, not parse.
    assert _parse_latlon("Boulder, Colorado") is None
    assert _parse_latlon("just words") is None


def test_parse_latlon_rejects_out_of_range():
    with pytest.raises(ValueError):
        _parse_latlon("200, 50")  # latitude too large
    with pytest.raises(ValueError):
        _parse_latlon("40, 200")  # longitude too large


def test_geocode_accepts_coordinates_without_network():
    loc = geocode("40.015, -105.27")
    assert loc.latitude == pytest.approx(40.015)
    assert loc.longitude == pytest.approx(-105.27)


def test_geocode_rejects_empty_and_placeholder():
    with pytest.raises(ValueError):
        geocode("")
    with pytest.raises(ValueError):
        geocode("CHANGE_ME, Your City")
