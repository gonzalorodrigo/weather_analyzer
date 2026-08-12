"""CLI: analyze historical wind to find the calmest hours for watering.

Usage:
    python main.py                          # uses config.py defaults
    python main.py --location "Boulder, Colorado" --years 5
    python main.py --location "40.015, -105.27" --no-cache
"""

from __future__ import annotations

import argparse
import sys

import requests

from config import DEFAULT_CONFIG, Config
from weather_analyzer import analyze, fetch, plots, report
from weather_analyzer.geocode import geocode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
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


def run(cfg: Config, use_cache: bool = True) -> int:
    """Execute the full pipeline. Returns a process exit code."""
    try:
        loc = geocode(cfg.location)
    except ValueError as exc:
        print(f"Location error: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"Network error while geocoding: {exc}", file=sys.stderr)
        return 1

    print(f"Location: {loc.name} ({loc.latitude:.4f}, {loc.longitude:.4f})")

    unit = cfg.wind_speed_unit
    start_date, end_date = fetch.default_date_range(cfg.years)
    try:
        df = fetch.fetch_wind(
            loc.latitude,
            loc.longitude,
            start_date,
            end_date,
            unit=unit,
            cache_dir=cfg.cache_dir,
            use_cache=use_cache,
        )
    except requests.RequestException as exc:
        print(f"Network error while fetching data: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return 1

    print(f"Got {len(df):,} hourly observations. Analyzing...")
    hourly = analyze.by_hour(df)
    matrix = analyze.by_month_hour(df)

    text = report.build_report(df, hourly, loc.name, unit, cfg.years)
    summary_path = report.write_report(text, cfg.output_dir)
    heatmap_path = plots.heatmap(matrix, loc.name, unit, cfg.output_dir)
    bar_path = plots.hourly_bar(hourly, loc.name, unit, cfg.output_dir)

    print()
    print(text)
    print(f"Saved summary : {summary_path}")
    print(f"Saved heatmap : {heatmap_path}")
    print(f"Saved bar chart: {bar_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = Config(
        location=args.location,
        years=args.years,
        wind_speed_unit=args.unit,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
    )
    return run(cfg, use_cache=not args.no_cache)


if __name__ == "__main__":
    raise SystemExit(main())
