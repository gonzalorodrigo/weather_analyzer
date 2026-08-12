"""Generate charts: a month x hour wind heatmap and an overall hourly bar chart.

Uses the non-interactive Agg backend so it works headless (no display needed).
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow backend selection)
import pandas as pd  # noqa: E402

from . import analyze  # noqa: E402
from . import solar  # noqa: E402
from .report import RADIATION_LABEL, UNIT_LABELS  # noqa: E402


def heatmap(
    matrix: pd.DataFrame, location_name: str, unit: str, output_dir: str
) -> str:
    """Save a month (rows) x hour (cols) heatmap of mean wind speed."""
    label = UNIT_LABELS.get(unit, unit)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "wind_heatmap.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(matrix.values, aspect="auto", origin="upper", cmap="YlGnBu")

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_yticks(range(12))
    ax.set_yticklabels(analyze.MONTH_NAMES)
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel("Month")
    ax.set_title(f"Mean wind speed by hour and month — {location_name}")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"Mean wind speed ({label})")

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def hourly_bar(
    hourly: pd.DataFrame, location_name: str, unit: str, output_dir: str
) -> str:
    """Save a bar chart of overall mean wind speed by hour of day."""
    label = UNIT_LABELS.get(unit, unit)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "wind_by_hour.png")

    speeds = hourly["mean_speed"].reindex(range(24))
    calm = set(analyze.calmest_hours(hourly, n=5))
    colors = ["#2a9d8f" if h in calm else "#adb5bd" for h in range(24)]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(24), speeds.values, color=colors)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel(f"Mean wind speed ({label})")
    ax.set_title(f"Mean wind speed by hour — {location_name} (calmest 5 highlighted)")
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# --- Solar radiation charts -------------------------------------------------


def sun_heatmap(
    matrix: pd.DataFrame, location_name: str, output_dir: str
) -> str:
    """Save a month (rows) x hour (cols) heatmap of mean solar radiation."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "sun_heatmap.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(matrix.values, aspect="auto", origin="upper", cmap="inferno")

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_yticks(range(12))
    ax.set_yticklabels(analyze.MONTH_NAMES)
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel("Month")
    ax.set_title(f"Mean solar radiation by hour and month — {location_name}")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"Mean solar radiation ({RADIATION_LABEL})")

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def sun_hourly_bar(
    hourly: pd.DataFrame,
    location_name: str,
    output_dir: str,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> str:
    """Save a bar chart of mean radiation by hour.

    Night hours (below the daylight threshold) are greyed; the weakest-sun
    daylight hours are highlighted.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "sun_by_hour.png")

    values = hourly["mean_radiation"].reindex(range(24))
    daylight = set(solar.daylight_hours(hourly, threshold))
    weak = set(solar.least_sun_daylight_hours(hourly, n=5, threshold=threshold))

    def _color(h: int) -> str:
        if h in weak:
            return "#e76f51"  # weakest-sun daylight hours
        if h in daylight:
            return "#f4a261"  # other daylight hours
        return "#cdd0d4"  # night

    colors = [_color(h) for h in range(24)]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(24), values.values, color=colors)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel(f"Mean solar radiation ({RADIATION_LABEL})")
    ax.set_title(
        f"Mean solar radiation by hour — {location_name} "
        "(weakest-sun daylight hours highlighted)"
    )
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# --- Wind vs sun comparison chart -------------------------------------------

WIND_COLOR = "#2a9d8f"
SUN_COLOR = "#e76f51"


def wind_sun_overlay(
    wind_hourly: pd.DataFrame,
    sun_hourly: pd.DataFrame,
    location_name: str,
    unit: str,
    output_dir: str,
) -> str:
    """Save a dual-axis chart comparing mean wind and mean sun by hour of day.

    Wind (left axis) and solar radiation (right axis) are on different scales,
    so each gets its own y-axis; the shared x-axis is the hour of day.
    """
    label = UNIT_LABELS.get(unit, unit)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "wind_sun_by_hour.png")

    hours = range(24)
    wind = wind_hourly["mean_speed"].reindex(hours)
    sun = sun_hourly["mean_radiation"].reindex(hours)

    fig, ax_wind = plt.subplots(figsize=(12, 5))
    ax_sun = ax_wind.twinx()

    (l_wind,) = ax_wind.plot(
        hours, wind.values, color=WIND_COLOR, marker="o", label=f"Wind ({label})"
    )
    (l_sun,) = ax_sun.plot(
        hours, sun.values, color=SUN_COLOR, marker="s",
        label=f"Sun ({RADIATION_LABEL})",
    )

    ax_wind.set_xticks(list(hours))
    ax_wind.set_xticklabels([f"{h:02d}" for h in hours])
    ax_wind.set_xlabel("Hour of day (local)")
    ax_wind.set_ylabel(f"Mean wind speed ({label})", color=WIND_COLOR)
    ax_sun.set_ylabel(f"Mean solar radiation ({RADIATION_LABEL})", color=SUN_COLOR)
    ax_wind.tick_params(axis="y", labelcolor=WIND_COLOR)
    ax_sun.tick_params(axis="y", labelcolor=SUN_COLOR)
    ax_wind.set_ylim(bottom=0)
    ax_sun.set_ylim(bottom=0)
    ax_wind.set_title(f"Wind vs sun by hour — {location_name}")
    ax_wind.grid(axis="y", linestyle=":", alpha=0.4)
    ax_wind.legend(handles=[l_wind, l_sun], loc="upper left")

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
