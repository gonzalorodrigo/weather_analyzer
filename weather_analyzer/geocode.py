"""Turn a location string into coordinates.

Accepts either a place name (geocoded via Open-Meteo's free geocoding API) or a
literal "lat, lon" pair, which is parsed directly without a network call.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Optional

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Matches "40.015, -105.27" / "40.015 -105.27" and similar.
_LATLON_RE = re.compile(
    r"^\s*(?P<lat>[-+]?\d+(?:\.\d+)?)\s*[, ]\s*(?P<lon>[-+]?\d+(?:\.\d+)?)\s*$"
)


class Location(NamedTuple):
    latitude: float
    longitude: float
    name: str


def _parse_latlon(location: str) -> Optional[Location]:
    """Return a Location if ``location`` is a bare "lat, lon" pair, else None."""
    match = _LATLON_RE.match(location)
    if not match:
        return None
    lat = float(match.group("lat"))
    lon = float(match.group("lon"))
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError(
            f"Coordinates out of range: lat={lat}, lon={lon} "
            "(expected lat in [-90, 90], lon in [-180, 180])."
        )
    return Location(lat, lon, f"{lat:.4f}, {lon:.4f}")


def geocode(location: str, timeout: float = 15.0) -> Location:
    """Resolve ``location`` to a :class:`Location`.

    Raises ValueError for a placeholder/empty value or when a place name cannot
    be found, and requests.RequestException on network/HTTP failure.
    """
    location = (location or "").strip()
    if not location or location.startswith("CHANGE_ME"):
        raise ValueError(
            "No location set. Edit config.py (or pass --location) with your city "
            'or coordinates, e.g. "Boulder, Colorado" or "40.015, -105.27".'
        )

    direct = _parse_latlon(location)
    if direct is not None:
        return direct

    resp = requests.get(
        GEOCODING_URL,
        params={"name": location, "count": 1, "language": "en", "format": "json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    results = resp.json().get("results") or []
    if not results:
        raise ValueError(
            f'Could not geocode location {location!r}. Try a nearby larger town, '
            'add the state/country, or pass coordinates as "lat, lon".'
        )

    top = results[0]
    name_parts = [
        str(top[key])
        for key in ("name", "admin1", "country")
        if top.get(key)
    ]
    return Location(
        latitude=float(top["latitude"]),
        longitude=float(top["longitude"]),
        name=", ".join(name_parts) or location,
    )
