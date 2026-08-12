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
from .report import UNIT_LABELS  # noqa: E402


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
