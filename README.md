# weather_analyzer

Find the best hours of the day to water at your location from historical weather data:

- **Least wind** — so watering has less spray drift and more even coverage.
- **Least sun** (among daylight hours) — so less water is lost to solar evaporation.

It pulls several years of **hourly data** from the free
[Open-Meteo](https://open-meteo.com/) archive (ERA5 reanalysis — no API key required),
then reports the best hours overall and month-by-month, with charts.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Both analyses (wind + sun) for a place by name (geocoded automatically):
python main.py --location "Boulder, Colorado" --years 5

# Just one metric:
python main.py --metric sun --location "Boulder, Colorado"
python main.py --metric wind --location "40.015, -105.27"

# Compare wind vs sun for every hour (overlay chart + combined best-hours):
python main.py --metric compare --location "Boulder, Colorado"

# Year overview: wind + sun across hour AND month (3 charts):
python main.py --metric overview --location "Boulder, Colorado"

# Force a fresh download instead of using the local cache:
python main.py --location "Boulder, Colorado" --no-cache
```

Set your own default location once by editing `location` in **`config.py`**, then just run
`python main.py`.

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--metric` | `both` | Which analysis: `wind`, `sun`, `both`, `compare`, or `overview` |
| `--location` | from `config.py` | Place name or `"lat, lon"` |
| `--years` | 5 | Years of history to analyze |
| `--unit` | `kmh` | Wind speed unit: `kmh`, `ms`, `mph`, `kn` (wind only) |
| `--cache-dir` | `data` | Where raw API pulls are cached |
| `--output-dir` | `output` | Where the reports and charts are written |
| `--no-cache` | off | Ignore the cache and re-fetch |

## Output

Written to `output/` (git-ignored):

**Wind** (`--metric wind` or `both`):
- **`wind_summary.txt`** — recommendation (calmest 3-hour window), calmest hours by month,
  and a ranked table of all 24 hours.
- **`wind_heatmap.png`** — month × hour heatmap of mean wind speed.
- **`wind_by_hour.png`** — mean wind speed by hour, calmest hours highlighted.

**Sun** (`--metric sun` or `both`):
- **`sun_summary.txt`** — daylight span, the least-sun *daylight* hours overall and by
  month, and a table of mean radiation per hour (with a daylight flag).
- **`sun_heatmap.png`** — month × hour heatmap of mean solar radiation.
- **`sun_by_hour.png`** — mean solar radiation by hour; night greyed, weakest-sun daylight
  hours highlighted.

**Compare** (`--metric compare`):
- **`compare_summary.txt`** — the best watering hours (low wind *and* low daylight sun),
  plus a side-by-side table of mean wind and mean sun for every hour.
- **`wind_sun_by_hour.png`** — dual-axis chart overlaying mean wind (left axis) and mean
  solar radiation (right axis) against hour of day.

**Overview** (`--metric overview`) — wind + sun across hour *and* month:
- **`overview_summary.txt`** — best watering hour per month, and the overall best
  (month, hour) cells.
- **`overview_bubble.png`** — month × hour bubble grid: dot **colour = sun**, dot
  **size = wind** (all four variables in one view).
- **`overview_daily_curves.png`** — 3×4 small multiples, one dual-axis daily curve per
  month (shared scales), showing how the wind/sun rhythm shifts through the year.
- **`overview_suitability.png`** — month × hour heatmap of the combined watering score
  (greener = calmer & less sun; grey = night).

Nighttime has ~0 sun, so the sun analysis filters to **daylight** and ranks within it —
the weak-sun hours it surfaces are the dawn/dusk edges, not the middle of the night.

Raw hourly data is cached in `data/` (git-ignored) so re-runs are instant.

## Tests

```bash
pip install pytest
python -m pytest
```

Tests run on synthetic data — no network needed.

## How it works

- `weather_analyzer/geocode.py` — place name → coordinates (or parse `"lat, lon"`).
- `weather_analyzer/fetch.py` — download hourly wind / solar radiation, cache to CSV.
- `weather_analyzer/analyze.py` — wind: group by hour and month × hour; find calmest hours.
- `weather_analyzer/solar.py` — sun: daylight detection and least-sun daylight hours.
- `weather_analyzer/report.py` — build the wind and sun text reports.
- `weather_analyzer/plots.py` — render the wind and sun charts.
- `main.py` — CLI wiring it all together (`--metric`).

## Notes

- Times are **local** to the location (`timezone=auto`, DST-aware) — essential for a
  "which hour of day" question.
- Wind is measured at 10 m (ERA5 standard); absolute values differ from sprinkler height
  but the *hourly trend* is what matters here.
- Sun uses **shortwave solar radiation** (W/m²); "daylight" is any hour whose mean
  irradiance clears a small threshold (~5 W/m²), so dawn/dusk count but night does not.
- Targets **Python 3.9+**.
