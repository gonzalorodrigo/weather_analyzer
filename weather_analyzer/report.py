"""Build the human-readable report: a ranked hour table plus a text summary."""

from __future__ import annotations

import os
from typing import List

import pandas as pd

from . import analyze
from . import solar

UNIT_LABELS = {"kmh": "km/h", "ms": "m/s", "mph": "mph", "kn": "kn"}
RADIATION_LABEL = "W/m²"


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


# --- Solar radiation report -------------------------------------------------


def sun_hour_table(hourly: pd.DataFrame, daylight: set[int]) -> str:
    """Chronological table of mean radiation per hour with a daylight flag."""
    lines = [
        f"{'hour':>5}  {'mean ' + RADIATION_LABEL:>12}  "
        f"{'median ' + RADIATION_LABEL:>14}  {'daylight':>8}",
        f"{'-' * 5}  {'-' * 12}  {'-' * 14}  {'-' * 8}",
    ]
    for hour in range(24):
        if hour not in hourly.index:
            continue
        row = hourly.loc[hour]
        mean = row["mean_radiation"]
        median = row["median_radiation"]
        mean_str = f"{mean:>12.1f}" if pd.notna(mean) else f"{'n/a':>12}"
        median_str = f"{median:>14.1f}" if pd.notna(median) else f"{'n/a':>14}"
        flag = "yes" if hour in daylight else "no"
        lines.append(f"{_fmt_hour(hour):>5}  {mean_str}  {median_str}  {flag:>8}")
    return "\n".join(lines)


def build_sun_report(
    df: pd.DataFrame,
    hourly: pd.DataFrame,
    location_name: str,
    years: int,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> str:
    """Assemble the full solar-radiation text report as a single string."""
    daylight = solar.daylight_hours(hourly, threshold)
    sections = []
    sections.append(f"Sun (solar radiation) analysis for {location_name}")
    sections.append(
        f"Based on ~{years} year(s) of hourly data ({len(df):,} observations)."
    )
    sections.append("")

    if not daylight:
        sections.append(
            f"No hour averaged above {threshold} {RADIATION_LABEL} — not enough sun "
            "to identify daylight hours for this location/period."
        )
        sections.append("")
        sections.append("=== Mean solar radiation by hour ===")
        sections.append(sun_hour_table(hourly, set(daylight)))
        sections.append("")
        return "\n".join(sections)

    first, last, peak = solar.daylight_span(hourly, threshold)
    weak = solar.least_sun_daylight_hours(hourly, n=5, threshold=threshold)
    by_month = solar.least_sun_daylight_by_month(df, n=3, threshold=threshold)
    weak_str = ", ".join(_fmt_hour(h) for h in weak)

    sections.append("=== Recommendation ===")
    sections.append(
        f"Sun is up roughly {_fmt_window(first, last)} (irradiance peaks near "
        f"{_fmt_hour(peak)}). Averaged over the period, the sun is weakest at the "
        "edges of the day."
    )
    sections.append(
        f"Five least-sun daylight hours overall: {weak_str}. "
        "Watering then means the least solar drying while the sun is up."
    )
    sections.append("")
    sections.append("=== Least-sun daylight hours by month ===")
    for month in range(1, 13):
        if month in by_month and by_month[month]:
            hours = ", ".join(_fmt_hour(h) for h in by_month[month])
            sections.append(f"  {analyze.MONTH_NAMES[month - 1]}: {hours}")
    sections.append("")
    sections.append("=== Mean solar radiation by hour ===")
    sections.append(sun_hour_table(hourly, set(daylight)))
    sections.append("")
    return "\n".join(sections)


# --- Wind vs sun comparison -------------------------------------------------


def _normalize(series: pd.Series) -> pd.Series:
    """Scale a series to [0, 1]; a flat series maps to all zeros."""
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or hi == lo:
        return series * 0.0
    return (series - lo) / (hi - lo)


def combined_watering_hours(
    wind_hourly: pd.DataFrame,
    sun_hourly: pd.DataFrame,
    n: int = 3,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> List[int]:
    """Daylight hours that are best on BOTH low wind and low sun, best first.

    Wind speed and radiation are each normalized to [0, 1] across the daylight
    hours and summed; the lowest combined score wins. Restricted to daylight so
    the recommendation is an actual watering time, not the middle of the night.
    """
    daylight = solar.daylight_hours(sun_hourly, threshold)
    if not daylight:
        return []
    wind = wind_hourly["mean_speed"].reindex(daylight)
    sun = sun_hourly["mean_radiation"].reindex(daylight)
    combined = (_normalize(wind) + _normalize(sun)).dropna().sort_values()
    return [int(h) for h in combined.index[:n]]


def compare_table(
    wind_hourly: pd.DataFrame, sun_hourly: pd.DataFrame, unit: str, daylight: set[int]
) -> str:
    """Side-by-side table of mean wind and mean sun for each hour of day."""
    label = UNIT_LABELS.get(unit, unit)
    lines = [
        f"{'hour':>5}  {'wind ' + label:>12}  {'sun ' + RADIATION_LABEL:>12}  "
        f"{'daylight':>8}",
        f"{'-' * 5}  {'-' * 12}  {'-' * 12}  {'-' * 8}",
    ]
    speeds = wind_hourly["mean_speed"].reindex(range(24))
    rad = sun_hourly["mean_radiation"].reindex(range(24))
    for hour in range(24):
        w = speeds.get(hour)
        s = rad.get(hour)
        w_str = f"{w:>12.1f}" if pd.notna(w) else f"{'n/a':>12}"
        s_str = f"{s:>12.1f}" if pd.notna(s) else f"{'n/a':>12}"
        flag = "yes" if hour in daylight else "no"
        lines.append(f"{_fmt_hour(hour):>5}  {w_str}  {s_str}  {flag:>8}")
    return "\n".join(lines)


def build_comparison_report(
    wind_hourly: pd.DataFrame,
    sun_hourly: pd.DataFrame,
    location_name: str,
    unit: str,
    years: int,
    observations: int,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> str:
    """Assemble the wind-vs-sun comparison report as a single string."""
    daylight = set(solar.daylight_hours(sun_hourly, threshold))
    best = combined_watering_hours(wind_hourly, sun_hourly, n=3, threshold=threshold)

    sections = []
    sections.append(f"Wind vs sun comparison for {location_name}")
    sections.append(
        f"Based on ~{years} year(s) of hourly data ({observations:,} observations)."
    )
    sections.append("")
    sections.append("=== Best watering hours (low wind + low daylight sun) ===")
    if best:
        best_str = ", ".join(_fmt_hour(h) for h in best)
        sections.append(
            f"{best_str} — calmest wind while the sun is still weak, for the least "
            "drift and evaporation."
        )
    else:
        sections.append("No daylight hours found for this location/period.")
    sections.append("")
    sections.append("=== Mean wind vs mean sun by hour ===")
    sections.append(compare_table(wind_hourly, sun_hourly, unit, daylight))
    sections.append("")
    return "\n".join(sections)


# --- Year overview: wind + sun across hour and month ------------------------


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Scale a whole DataFrame to [0, 1] over its non-NaN values."""
    vmin = df.min().min()
    vmax = df.max().max()
    if pd.isna(vmin) or vmax == vmin:
        return df * 0.0
    return (df - vmin) / (vmax - vmin)


def suitability_matrix(
    wind_matrix: pd.DataFrame,
    sun_matrix: pd.DataFrame,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> pd.DataFrame:
    """Combined watering score per (month, hour); lower = better.

    Restricted to daylight cells (mean radiation above ``threshold``); other
    cells are NaN. Wind and radiation are each normalized to [0, 1] across the
    daylight cells and summed, so a low score means calm AND low sun.
    """
    daylight = sun_matrix > threshold
    wind = wind_matrix.where(daylight)
    sun = sun_matrix.where(daylight)
    return _normalize_frame(wind) + _normalize_frame(sun)


def best_hour_per_month(score_matrix: pd.DataFrame) -> "dict[int, int]":
    """Map each month to the hour with the best (lowest) suitability score."""
    result: dict[int, int] = {}
    for month, row in score_matrix.iterrows():
        if row.notna().any():
            result[int(month)] = int(row.idxmin())
    return result


def build_overview_report(
    wind_matrix: pd.DataFrame,
    sun_matrix: pd.DataFrame,
    location_name: str,
    years: int,
    observations: int,
    threshold: float = solar.DEFAULT_DAYLIGHT_THRESHOLD,
) -> str:
    """Assemble the year-overview text report (best watering cells)."""
    score = suitability_matrix(wind_matrix, sun_matrix, threshold)
    by_month = best_hour_per_month(score)

    sections = []
    sections.append(f"Year overview (wind + sun by hour and month) for {location_name}")
    sections.append(
        f"Based on ~{years} year(s) of hourly data ({observations:,} observations)."
    )
    sections.append("")
    sections.append("=== Best watering hour per month (calm + low daylight sun) ===")
    if by_month:
        for month in range(1, 13):
            if month in by_month:
                sections.append(
                    f"  {analyze.MONTH_NAMES[month - 1]}: {_fmt_hour(by_month[month])}"
                )
    else:
        sections.append("No daylight cells found for this location/period.")
    sections.append("")

    stacked = score.stack().sort_values()
    if not stacked.empty:
        sections.append("=== Overall best (month, hour) cells ===")
        for (month, hour), _ in stacked.head(5).items():
            sections.append(
                f"  {analyze.MONTH_NAMES[int(month) - 1]} {_fmt_hour(int(hour))}"
            )
        sections.append("")
    return "\n".join(sections)
