"""CLI: analyze historical weather to find the best hours for watering.

Reports the calmest hours (least wind) and/or the least-sun daylight hours for a
location, from Open-Meteo's historical archive.

Usage:
    python main.py                                   # both analyses, config defaults
    python main.py --metric sun --location "Boulder, Colorado"
    python main.py --metric wind --years 5
    python main.py --location "40.015, -105.27" --no-cache
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional, Tuple

import pandas as pd
import requests

from config import DEFAULT_CONFIG, Config
from weather_analyzer import analyze, fetch, plots, report, solar
from weather_analyzer.geocode import Location, geocode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--metric",
        default="both",
        choices=["wind", "sun", "both", "compare", "overview"],
        help="Which analysis to run (default: %(default)s). 'compare' overlays "
        "wind and sun by hour; 'overview' shows them across hour AND month.",
    )
    p.add_argument(
        "--location",
        default=DEFAULT_CONFIG.location,
        help='Place name or "lat, lon" (default: from config.py).',
    )
    p.add_argument(
        "--years",
        type=int,
        default=DEFAULT_CONFIG.years,
        help="Years of history to analyze (default: %(default)s).",
    )
    p.add_argument(
        "--unit",
        default=DEFAULT_CONFIG.wind_speed_unit,
        choices=["kmh", "ms", "mph", "kn"],
        help="Wind speed unit (default: %(default)s).",
    )
    p.add_argument("--cache-dir", default=DEFAULT_CONFIG.cache_dir)
    p.add_argument("--output-dir", default=DEFAULT_CONFIG.output_dir)
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore any cached data and re-fetch from the API.",
    )
    return p.parse_args(argv)


def _fetch(fetch_call: Callable[[], pd.DataFrame]) -> Tuple[Optional[pd.DataFrame], int]:
    """Run a fetch, mapping failures to (None, exit_code)."""
    try:
        return fetch_call(), 0
    except requests.RequestException as exc:
        print(f"Network error while fetching data: {exc}", file=sys.stderr)
        return None, 1
    except RuntimeError as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return None, 1


def _run_wind(
    loc: Location, start_date: str, end_date: str, cfg: Config, use_cache: bool
) -> int:
    unit = cfg.wind_speed_unit
    df, rc = _fetch(
        lambda: fetch.fetch_wind(
            loc.latitude, loc.longitude, start_date, end_date,
            unit=unit, cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc

    print(f"[wind] {len(df):,} hourly observations. Analyzing...")
    hourly = analyze.by_hour(df)
    matrix = analyze.by_month_hour(df)

    text = report.build_report(df, hourly, loc.name, unit, cfg.years)
    summary_path = report.write_report(text, cfg.output_dir, "wind_summary.txt")
    heatmap_path = plots.heatmap(matrix, loc.name, unit, cfg.output_dir)
    bar_path = plots.hourly_bar(hourly, loc.name, unit, cfg.output_dir)

    print()
    print(text)
    print(f"Saved wind summary : {summary_path}")
    print(f"Saved wind heatmap : {heatmap_path}")
    print(f"Saved wind bar chart: {bar_path}")
    return 0


def _run_sun(
    loc: Location, start_date: str, end_date: str, cfg: Config, use_cache: bool
) -> int:
    df, rc = _fetch(
        lambda: fetch.fetch_solar(
            loc.latitude, loc.longitude, start_date, end_date,
            cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc

    print(f"[sun] {len(df):,} hourly observations. Analyzing...")
    hourly = solar.by_hour(df)
    matrix = solar.by_month_hour(df)

    text = report.build_sun_report(df, hourly, loc.name, cfg.years)
    summary_path = report.write_report(text, cfg.output_dir, "sun_summary.txt")
    heatmap_path = plots.sun_heatmap(matrix, loc.name, cfg.output_dir)
    bar_path = plots.sun_hourly_bar(hourly, loc.name, cfg.output_dir)

    print()
    print(text)
    print(f"Saved sun summary : {summary_path}")
    print(f"Saved sun heatmap : {heatmap_path}")
    print(f"Saved sun bar chart: {bar_path}")
    return 0


def _run_compare(
    loc: Location, start_date: str, end_date: str, cfg: Config, use_cache: bool
) -> int:
    unit = cfg.wind_speed_unit
    wind_df, rc = _fetch(
        lambda: fetch.fetch_wind(
            loc.latitude, loc.longitude, start_date, end_date,
            unit=unit, cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc
    sun_df, rc = _fetch(
        lambda: fetch.fetch_solar(
            loc.latitude, loc.longitude, start_date, end_date,
            cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc

    print(f"[compare] {len(wind_df):,} + {len(sun_df):,} hourly observations. Analyzing...")
    wind_hourly = analyze.by_hour(wind_df)
    sun_hourly = solar.by_hour(sun_df)

    text = report.build_comparison_report(
        wind_hourly, sun_hourly, loc.name, unit, cfg.years, len(wind_df)
    )
    summary_path = report.write_report(text, cfg.output_dir, "compare_summary.txt")
    chart_path = plots.wind_sun_overlay(
        wind_hourly, sun_hourly, loc.name, unit, cfg.output_dir
    )

    print()
    print(text)
    print(f"Saved comparison summary: {summary_path}")
    print(f"Saved comparison chart  : {chart_path}")
    return 0


def _run_overview(
    loc: Location, start_date: str, end_date: str, cfg: Config, use_cache: bool
) -> int:
    unit = cfg.wind_speed_unit
    wind_df, rc = _fetch(
        lambda: fetch.fetch_wind(
            loc.latitude, loc.longitude, start_date, end_date,
            unit=unit, cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc
    sun_df, rc = _fetch(
        lambda: fetch.fetch_solar(
            loc.latitude, loc.longitude, start_date, end_date,
            cache_dir=cfg.cache_dir, use_cache=use_cache,
        )
    )
    if rc:
        return rc

    print(f"[overview] {len(wind_df):,} + {len(sun_df):,} hourly observations. Analyzing...")
    wind_matrix = analyze.by_month_hour(wind_df)
    sun_matrix = solar.by_month_hour(sun_df)
    score = report.suitability_matrix(wind_matrix, sun_matrix)

    text = report.build_overview_report(
        wind_matrix, sun_matrix, loc.name, cfg.years, len(wind_df)
    )
    summary_path = report.write_report(text, cfg.output_dir, "overview_summary.txt")
    bubble_path = plots.bubble_grid(wind_matrix, sun_matrix, loc.name, unit, cfg.output_dir)
    curves_path = plots.daily_curves(wind_matrix, sun_matrix, loc.name, unit, cfg.output_dir)
    heat_path = plots.suitability_heatmap(score, loc.name, cfg.output_dir)

    print()
    print(text)
    print(f"Saved overview summary    : {summary_path}")
    print(f"Saved bubble grid         : {bubble_path}")
    print(f"Saved daily curves        : {curves_path}")
    print(f"Saved suitability heatmap : {heat_path}")
    return 0


def run(cfg: Config, metric: str = "both", use_cache: bool = True) -> int:
    """Execute the selected pipeline(s). Returns a process exit code."""
    try:
        loc = geocode(cfg.location)
    except ValueError as exc:
        print(f"Location error: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"Network error while geocoding: {exc}", file=sys.stderr)
        return 1

    print(f"Location: {loc.name} ({loc.latitude:.4f}, {loc.longitude:.4f})")
    start_date, end_date = fetch.default_date_range(cfg.years)

    if metric == "compare":
        return _run_compare(loc, start_date, end_date, cfg, use_cache)
    if metric == "overview":
        return _run_overview(loc, start_date, end_date, cfg, use_cache)

    # Wind and sun are independent API calls, so run both even if one fails and
    # return the worst exit code — a wind failure shouldn't hide the sun report.
    rc = 0
    if metric in ("wind", "both"):
        rc = max(rc, _run_wind(loc, start_date, end_date, cfg, use_cache))
    if metric in ("sun", "both"):
        rc = max(rc, _run_sun(loc, start_date, end_date, cfg, use_cache))
    return rc


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = Config(
        location=args.location,
        years=args.years,
        wind_speed_unit=args.unit,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
    )
    return run(cfg, metric=args.metric, use_cache=not args.no_cache)


if __name__ == "__main__":
    raise SystemExit(main())
