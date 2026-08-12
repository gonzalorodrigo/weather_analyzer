"""Generate charts: a month x hour wind heatmap and an overall hourly bar chart.

Uses the non-interactive Agg backend so it works headless (no display needed).
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow backend selection)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import StrMethodFormatter  # noqa: E402

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


# --- Year overview: wind + sun across hour and month ------------------------


def bubble_grid(
    wind_matrix: pd.DataFrame,
    sun_matrix: pd.DataFrame,
    location_name: str,
    unit: str,
    output_dir: str,
) -> str:
    """Month x hour bubble grid: dot colour = mean sun, dot size = mean wind."""
    label = UNIT_LABELS.get(unit, unit)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "overview_bubble.png")

    wind_max = wind_matrix.max().max()
    xs, ys, sizes, colors = [], [], [], []
    for month in range(1, 13):
        for hour in range(24):
            w = wind_matrix.loc[month, hour]
            s = sun_matrix.loc[month, hour]
            if pd.isna(w) or pd.isna(s):
                continue
            xs.append(hour)
            ys.append(month)
            sizes.append(20 + 380 * (w / wind_max if wind_max else 0))
            colors.append(s)

    fig, ax = plt.subplots(figsize=(13, 6))
    sc = ax.scatter(
        xs, ys, s=sizes, c=colors, cmap="YlOrRd",
        edgecolors="0.35", linewidths=0.3, alpha=0.9,
    )
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_yticks(range(1, 13))
    ax.set_yticklabels(analyze.MONTH_NAMES)
    ax.invert_yaxis()  # January at the top, like the heatmaps
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel("Month")
    ax.set_title(
        f"Wind & sun by hour and month — {location_name}\n"
        "(dot colour = sun, dot size = wind)"
    )
    ax.margins(x=0.02, y=0.05)

    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label(f"Mean solar radiation ({RADIATION_LABEL})")

    handles, labels = sc.legend_elements(
        prop="sizes", num=4,
        func=lambda z: (z - 20) / 380 * wind_max,
        fmt=StrMethodFormatter("{x:.0f}"),
    )
    ax.legend(
        handles, labels,
        title=f"Wind ({label})", loc="center left", bbox_to_anchor=(1.18, 0.5),
        labelspacing=1.4, frameon=True,
    )

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def daily_curves(
    wind_matrix: pd.DataFrame,
    sun_matrix: pd.DataFrame,
    location_name: str,
    unit: str,
    output_dir: str,
) -> str:
    """3x4 small multiples: wind + sun daily curve for each month, shared scales."""
    label = UNIT_LABELS.get(unit, unit)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "overview_daily_curves.png")

    wind_max = wind_matrix.max().max() * 1.05 or 1.0
    sun_max = sun_matrix.max().max() * 1.05 or 1.0
    hours = range(24)

    fig, axes = plt.subplots(3, 4, figsize=(15, 8), sharex=True)
    l_wind = l_sun = None
    for i, month in enumerate(range(1, 13)):
        ax = axes.flat[i]
        ax2 = ax.twinx()
        (l_wind,) = ax.plot(
            hours, wind_matrix.loc[month].reindex(hours).values,
            color=WIND_COLOR, lw=1.6, label=f"Wind ({label})",
        )
        (l_sun,) = ax2.plot(
            hours, sun_matrix.loc[month].reindex(hours).values,
            color=SUN_COLOR, lw=1.6, label=f"Sun ({RADIATION_LABEL})",
        )
        ax.set_ylim(0, wind_max)
        ax2.set_ylim(0, sun_max)
        ax.set_title(analyze.MONTH_NAMES[month - 1], fontsize=10)
        ax.set_xticks([0, 6, 12, 18])
        # Only label wind axis on the left column, sun axis on the right column.
        if i % 4 != 0:
            ax.tick_params(labelleft=False)
        else:
            ax.set_ylabel(label, color=WIND_COLOR, fontsize=8)
        if i % 4 != 3:
            ax2.tick_params(labelright=False)
        else:
            ax2.set_ylabel(RADIATION_LABEL, color=SUN_COLOR, fontsize=8)

    fig.suptitle(
        f"Wind vs sun daily curve by month — {location_name}", fontsize=13
    )
    fig.legend(handles=[l_wind, l_sun], loc="lower center", ncol=2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def suitability_heatmap(
    score_matrix: pd.DataFrame, location_name: str, output_dir: str
) -> str:
    """Month x hour heatmap of the combined watering score (greener = better)."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "overview_suitability.png")

    cmap = plt.get_cmap("RdYlGn_r").copy()
    cmap.set_bad("#e9ecef")  # night / no-daylight cells

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(
        np.ma.masked_invalid(score_matrix.values),
        aspect="auto", origin="upper", cmap=cmap,
    )
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_yticks(range(12))
    ax.set_yticklabels(analyze.MONTH_NAMES)
    ax.set_xlabel("Hour of day (local)")
    ax.set_ylabel("Month")
    ax.set_title(
        f"Watering suitability by hour and month — {location_name}\n"
        "(greener = calmer & less sun; grey = night)"
    )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Combined score (lower = better)")

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
