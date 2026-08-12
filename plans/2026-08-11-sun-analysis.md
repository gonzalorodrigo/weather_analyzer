# Sun (Solar Radiation) Analysis — Plan

_Recorded 2026-08-11. Follow-on to the wind analyzer._

## Context

The wind tool finds the calmest hours for watering. This adds a parallel analysis of
**which daylight hours have the least sun**, using hourly **shortwave solar radiation**
(W/m²) from the same Open-Meteo archive. Pairing low wind + low sun points at the hours
with the least evaporative loss.

Decisions (from Q&A): report **least-sun *daylight* hours** (nighttime is trivially zero,
so it's filtered out; charts still show the full 24h curve). Structure as a **new solar
module reusing the existing geocode/fetch/caching, with a shared CLI**.

## Changes

- **`weather_analyzer/fetch.py`** — extract shared `_fetch_hourly(...)` (HTTP + cache +
  DataFrame build). Keep `fetch_wind` as a thin wrapper; add
  `fetch_solar(...)` for `shortwave_radiation`. Cache files prefixed `wind_` / `solar_`.
- **`weather_analyzer/solar.py`** (new) — analysis:
  - `by_hour` (mean/median radiation per hour), `by_month_hour` (matrix for heatmap).
  - `daylight_hours(hourly, threshold)` — hours whose mean radiation exceeds a small
    threshold (default 5 W/m²), i.e. sun is up.
  - `least_sun_daylight_hours(hourly, n, threshold)` — daylight hours ranked ascending
    (dawn/dusk edges surface). Excludes night by construction.
  - `daylight_span(hourly, threshold)` → (first, last, peak) hours for the summary.
  - `least_sun_daylight_by_month(df, n, threshold)`.
- **`weather_analyzer/report.py`** — add `build_sun_report(...)` and a chronological
  `sun_hour_table` (hour, mean W/m², daylight flag). Reuse `write_report`.
- **`weather_analyzer/plots.py`** — add `sun_heatmap` (month×hour, warm cmap) and
  `sun_hourly_bar` (weakest daylight hours highlighted).
- **`main.py`** — add `--metric {wind,sun,both}` (default `both`). Resolve location + date
  range once, then run selected pipelines. Wind summary → `wind_summary.txt`, sun →
  `sun_summary.txt`; sun charts → `sun_heatmap.png`, `sun_by_hour.png`.
- **`tests/test_solar.py`** (new) — synthetic day/night radiation; assert daylight
  detection, that least-sun hours are the dawn/dusk edges (not night), and matrix shapes.
- **README** — document `--metric` and the sun outputs.

## Verification

- `python -m pytest` (all wind + solar tests, no network).
- `python main.py --metric sun --location "Boulder, Colorado"` — sanity: daylight ~05–20
  in summer-inclusive average, sun weakest at the daylight edges, peak near solar noon.
- `python main.py --metric both ...` — both reports + 4 charts.
- Run `code-reviewer` agent and apply findings before commit (per CLAUDE.md).

## Notes

- Daylight threshold is a small absolute irradiance (5 W/m²) so dawn/dusk count as daylight
  but true night (≈0) is excluded. Configurable.
- `timezone=auto` keeps hours local (as with wind).
