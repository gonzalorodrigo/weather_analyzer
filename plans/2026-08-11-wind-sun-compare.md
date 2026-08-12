# Wind vs Sun Comparison — Plan

_Recorded 2026-08-11. Follow-on to the wind + sun analyses._

## Context

Compare **wind speed** and **sun intensity** for every hour of the day, so the two
watering signals can be read together. Adds a `compare` mode that overlays both on one
chart and recommends the hours that are good on both (calm + low daylight sun).

## Changes

- **`report.py`**
  - `combined_watering_hours(wind_hourly, sun_hourly, n, threshold)` — normalize wind and
    radiation to [0,1] across **daylight** hours, sum, pick the lowest (best on both).
  - `compare_table(wind_hourly, sun_hourly, unit, daylight)` — hour | mean wind | mean sun
    | daylight flag, chronological.
  - `build_comparison_report(...)` — best-hours line + the table.
- **`plots.py`** — `wind_sun_overlay(...)`: dual-axis line chart (wind left, sun right,
  hour on x) → `wind_sun_by_hour.png`.
- **`main.py`** — add `--metric compare`; `_run_compare` fetches both wind + solar (reusing
  cache), builds the report + chart. Outputs `compare_summary.txt`, `wind_sun_by_hour.png`.
- **`tests/test_compare.py`** — combined-hours logic (daylight-only, excludes windiest and
  sunniest, empty without daylight) + table shape. No network.
- **README** — document `compare`.

## Verification

- `python -m pytest` (all metrics, no network).
- `python main.py --metric compare` — sanity: overlay chart written; best watering hours
  are calm daylight hours (not noon, not night).
- Run `code-reviewer` agent and apply findings before commit.

## Notes

- Dual y-axes because wind (km/h) and radiation (W/m²) have different scales/units.
- Reuses `solar.daylight_hours` so the recommendation is a real daytime watering slot.
