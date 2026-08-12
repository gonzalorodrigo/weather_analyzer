# Year Overview Visualizations — Plan

_Recorded 2026-08-11. Follow-on to the compare feature._

## Context

Compare **wind, sun, hour of day, and month** together. Adds a `--metric overview` mode
producing three complementary views of the month × hour grid:

1. **Bubble grid** — dot colour = mean sun, dot size = mean wind (all four in one view).
2. **Daily-curve small multiples** — 3×4 grid, a dual-axis wind+sun daily curve per month
   (shared scales) to show how the daily rhythm shifts seasonally.
3. **Suitability heatmap** — month × hour coloured by a combined watering score
   (normalized wind + sun over daylight cells; greener = better; night = grey).

## Changes

- **report.py** — `_normalize_frame`, `suitability_matrix(wind_matrix, sun_matrix)`
  (daylight-only combined score), `best_hour_per_month`, `build_overview_report`.
- **plots.py** — `bubble_grid`, `daily_curves`, `suitability_heatmap` (+ numpy for masked
  night cells; `StrMethodFormatter` for the size legend).
- **main.py** — `--metric overview` + `_run_overview` (fetch wind + solar, build matrices +
  score, 3 charts + summary).
- **tests/test_overview.py** — suitability masks night, best-hour is daylight/not-noon,
  `_normalize_frame` flat/NaN handling, empty-without-daylight. No network.
- **README** — document `overview`.

Outputs: `overview_summary.txt`, `overview_bubble.png`, `overview_daily_curves.png`,
`overview_suitability.png`.

## Verification

- `python -m pytest` (no network).
- `python main.py --metric overview` — visually inspect all three PNGs (done: clean).
- `code-reviewer` agent + apply findings before commit; exclude local `config.py`.

## Notes

- Suitability restricted to daylight (via the same `> threshold` rule as solar), so night
  cells are masked, not scored.
- Combined score normalizes wind and sun independently across daylight cells, then sums —
  low = calm AND low sun.
