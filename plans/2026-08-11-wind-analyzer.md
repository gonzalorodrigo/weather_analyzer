# Weather Wind Analyzer — Plan

_Recorded 2026-08-11. Source of truth for the initial build._

## Context

Goal: find **which hours of the day tend to have the least/weakest wind** at the user's
home, so watering can be scheduled then (low wind = less spray drift, more even coverage,
less evaporation). The tool fetches **historical hourly wind data** for a location and
analyzes it to surface the calmest hours — overall and month-by-month (watering needs
shift with the seasons).

Greenfield project. Local Python is **3.9.6** (avoid 3.10+ only syntax and `tomllib`).

## Data source

**Open-Meteo** — free, no API key, hourly resolution:

- **Historical archive** (ERA5 reanalysis): `https://archive-api.open-meteo.com/v1/archive`
  - Params: `latitude`, `longitude`, `start_date`, `end_date`, `timezone=auto`
    (hours in *local* time — essential), `wind_speed_unit=kmh` (configurable),
    `hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m`.
  - 5 years hourly ≈ 44k rows — one request, fits in memory.
- **Geocoding** (city/address → lat/lon): `https://geocoding-api.open-meteo.com/v1/search`

Chosen settings: **5 years** history, breakdown **by month + overall**, output
**charts + table + text summary**.

## Project structure

```
weather_analyzer/
├── README.md                 # setup + usage (rewrite)
├── requirements.txt          # requests, pandas, matplotlib
├── config.py                 # LOCATION (edit this!), YEARS, units, output paths
├── main.py                   # CLI entry point; orchestrates the pipeline
├── weather_analyzer/
│   ├── __init__.py
│   ├── geocode.py            # location string -> (lat, lon, resolved name)
│   ├── fetch.py              # download hourly wind; cache raw CSV to data/
│   ├── analyze.py            # pandas: group by hour and by (month, hour)
│   ├── report.py             # ranked table + plain-text recommendation
│   └── plots.py              # heatmap + hourly bar chart -> output/
├── data/                     # cached raw API responses (git-ignored)
├── output/                   # generated charts (git-ignored)
└── tests/
    └── test_analyze.py       # unit tests on synthetic data (no network)
```

`config.py` holds a simple dataclass with defaults; CLI flags (`--location`, `--years`)
override them.

## How each piece works

- **config.py** — `Config` dataclass: `location` (default placeholder
  `"CHANGE_ME, Your City"`), `years=5`, `wind_speed_unit="kmh"`, `cache_dir="data"`,
  `output_dir="output"`. The one line the user edits with their real address.
- **geocode.py** — `geocode(location) -> (lat, lon, name)`. If `location` already looks
  like `"lat, lon"`, parse directly and skip the API call.
- **fetch.py** — `fetch_wind(lat, lon, start, end, unit) -> DataFrame`. Compute dates from
  `years`. **Cache** raw pull to `data/wind_<lat>_<lon>_<start>_<end>.csv`; reuse if
  present. Returns DataFrame indexed by local timestamp with `wind_speed_10m`,
  `wind_gusts_10m`, `wind_direction_10m`.
- **analyze.py** — add `hour`/`month` columns; then `by_hour` (mean+median speed, mean
  gust), `by_month_hour` (mean speed → heatmap matrix), `calmest_hours(n)` (rank ascending
  + calmest contiguous window; reused per-month).
- **report.py** — ranked table + text summary (overall calmest window; calmest hours per
  month / summer watering months). Writes `output/summary.txt`.
- **plots.py** — matplotlib: (1) heatmap month×hour colored by mean wind; (2) bar chart of
  overall mean wind by hour. PNGs to `output/`.
- **main.py** — `argparse` CLI: geocode → fetch (cached) → analyze → report + plots.

## Dependencies

`requirements.txt`: `requests`, `pandas`, `matplotlib`. CSV cache avoids parquet/pyarrow.
Venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

## Verification (end-to-end)

1. `pip install -r requirements.txt`.
2. `python main.py --location "Boulder, Colorado" --years 5` — geocoding, live fetch,
   cached CSV in `data/`, PNGs in `output/`, printed calmest-hours summary. Sanity: calm
   overnight/early morning, windier mid-afternoon.
3. Re-run → uses cache (near-instant, no network).
4. `python -m pytest` — synthetic DataFrame with a known low-wind hour; assert
   `calmest_hours()` returns it (no network).
5. Edit `config.py` `location` to the real address and run `python main.py`.

## Notes / decisions

- `timezone=auto` makes "hour of day" meaningful (local, DST-aware).
- Wind at 10 m is standard ERA5 height; good proxy for near-ground breeze *trends*.
- Future add-ons (out of scope): daylight-only filter, precipitation/temperature factors,
  `et0_fao_evapotranspiration` to co-optimize for evaporation.
