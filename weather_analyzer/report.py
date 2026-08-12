"""Build the human-readable report: a ranked hour table plus a text summary."""

from __future__ import annotations

import os

import pandas as pd

from . import analyze

UNIT_LABELS = {"kmh": "km/h", "ms": "m/s", "mph": "mph", "kn": "kn"}


def _fmt_hour(hour: int) -> str:
    return f"{hour:02d}:00"


def _fmt_window(start: int, end: int) -> str:
    # End hour is inclusive; show the close of that hour for readability.
    return f"{_fmt_hour(start)}–{_fmt_hour((end + 1) % 24)}"


def hour_table(hourly: pd.DataFrame, unit: str) -> str:
    """A fixed-width table of every hour ranked calmest-first."""
    label = UNIT_LABELS.get(unit, unit)
    ranked = hourly.dropna(subset=["mean_speed"]).sort_values("mean_speed")
    lines = [
        f"{'rank':>4}  {'hour':>5}  {'mean ' + label:>12}  "
        f"{'median ' + label:>14}  {'gust ' + label:>12}",
        f"{'-' * 4}  {'-' * 5}  {'-' * 12}  {'-' * 14}  {'-' * 12}",
    ]
    for rank, (hour, row) in enumerate(ranked.iterrows(), start=1):
        median = row["median_speed"]
        median_str = f"{median:>14.1f}" if pd.notna(median) else f"{'n/a':>14}"
        gust = row["mean_gust"]
        gust_str = f"{gust:>12.1f}" if pd.notna(gust) else f"{'n/a':>12}"
        lines.append(
            f"{rank:>4}  {_fmt_hour(int(hour)):>5}  {row['mean_speed']:>12.1f}  "
            f"{median_str}  {gust_str}"
        )
    return "\n".join(lines)


def build_report(
    df: pd.DataFrame,
    hourly: pd.DataFrame,
    location_name: str,
    unit: str,
    years: int,
) -> str:
    """Assemble the full text report as a single string."""
    label = UNIT_LABELS.get(unit, unit)
    calm = analyze.calmest_hours(hourly, n=5)
    start, end, win_mean = analyze.calmest_window(hourly, length=3)
    by_month = analyze.calmest_hours_by_month(df, n=3)

    calm_str = ", ".join(_fmt_hour(h) for h in calm)

    sections = []
    sections.append(f"Wind analysis for {location_name}")
    sections.append(f"Based on ~{years} year(s) of hourly data ({len(df):,} observations).")
    sections.append("")
    sections.append("=== Recommendation ===")
    sections.append(
        f"Calmest 3-hour window overall: {_fmt_window(start, end)} "
        f"(avg {win_mean:.1f} {label}). Water then for the least wind."
    )
    sections.append(f"Five calmest single hours overall: {calm_str}.")
    sections.append("")
    sections.append("=== Calmest hours by month ===")
    for month in range(1, 13):
        if month in by_month:
            hours = ", ".join(_fmt_hour(h) for h in by_month[month])
            sections.append(f"  {analyze.MONTH_NAMES[month - 1]}: {hours}")
    sections.append("")
    sections.append("=== All hours, calmest first ===")
    sections.append(hour_table(hourly, unit))
    sections.append("")
    return "\n".join(sections)


def write_report(text: str, output_dir: str, filename: str = "summary.txt") -> str:
    """Write the report to ``output_dir/filename`` and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path
