"""Configuration for the weather wind analyzer.

Edit ``DEFAULT_CONFIG.location`` to your home address (or "lat, lon"). Everything
here can also be overridden on the command line — see ``main.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    """User-editable settings for a run."""

    # Your location. A place name ("Boulder, Colorado") gets geocoded, or pass
    # coordinates directly as "lat, lon" (e.g. "40.015, -105.27").
    location: str = "CHANGE_ME, Your City"

    # How many years of historical hourly data to analyze.
    years: int = 5

    # Wind speed unit reported by Open-Meteo: "kmh", "ms", "mph", or "kn".
    wind_speed_unit: str = "kmh"

    # Where cached API pulls and generated charts go (relative to repo root).
    cache_dir: str = "data"
    output_dir: str = "output"


DEFAULT_CONFIG = Config()
