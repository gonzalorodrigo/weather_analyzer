# weather_analyzer

Find the **calmest hours of the day** at your location from historical weather data,
so you can schedule watering when wind is weakest (less spray drift, more even coverage,
less evaporation).

It pulls several years of **hourly wind data** from the free
[Open-Meteo](https://open-meteo.com/) archive (ERA5 reanalysis — no API key required),
then reports the calmest hours overall and month-by-month, with charts.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Analyze a place by name (geocoded automatically):
python main.py --location "Boulder, Colorado" --years 5

# Or pass coordinates directly (skips geocoding):
python main.py --location "40.015, -105.27"

# Force a fresh download instead of using the local cache:
python main.py --location "Boulder, Colorado" --no-cache
```

Set your own default location once by editing `location` in **`config.py`**, then just run
`python main.py`.

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--location` | from `config.py` | Place name or `"lat, lon"` |
| `--years` | 5 | Years of history to analyze |
| `--unit` | `kmh` | Wind speed unit: `kmh`, `ms`, `mph`, `kn` |
| `--cache-dir` | `data` | Where raw API pulls are cached |
| `--output-dir` | `output` | Where the report and charts are written |
| `--no-cache` | off | Ignore the cache and re-fetch |

## Output

Written to `output/` (git-ignored):

- **`summary.txt`** — recommendation (calmest 3-hour window), calmest hours by month, and a
  ranked table of all 24 hours.
- **`wind_heatmap.png`** — month × hour heatmap of mean wind speed (the calm "valley" is
  easy to spot).
- **`wind_by_hour.png`** — mean wind speed by hour, calmest hours highlighted.

Raw hourly data is cached in `data/` (git-ignored) so re-runs are instant.

## Tests

```bash
pip install pytest
python -m pytest
```

Tests run on synthetic data — no network needed.

## How it works

- `weather_analyzer/geocode.py` — place name → coordinates (or parse `"lat, lon"`).
- `weather_analyzer/fetch.py` — download hourly wind, cache to CSV.
- `weather_analyzer/analyze.py` — group by hour and by month × hour; find calmest hours.
- `weather_analyzer/report.py` — build the text report.
- `weather_analyzer/plots.py` — render the charts.
- `main.py` — CLI wiring it all together.

## Notes

- Times are **local** to the location (`timezone=auto`, DST-aware) — essential for a
  "which hour of day" question.
- Wind is measured at 10 m (ERA5 standard); absolute values differ from sprinkler height
  but the *hourly trend* is what matters here.
- Targets **Python 3.9+**.
