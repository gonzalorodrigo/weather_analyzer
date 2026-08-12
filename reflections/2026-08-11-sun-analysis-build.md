# Reflections — 2026-08-11 (sun analysis build)

Adding a solar-radiation analysis parallel to the wind analyzer.

## Design that worked
- "Least sun" is trivial at face value (night = 0 W/m²). The useful question is **least sun
  among daylight hours** — filter to hours whose mean irradiance clears a small threshold
  (5 W/m²), then rank within it. Night is excluded by construction; the weak-sun hours that
  surface are the dawn/dusk edges. A dedicated test asserts night never wins despite being
  the global minimum.
- Reuse paid off: extracted `_fetch_hourly` in fetch.py so `fetch_wind` and `fetch_solar`
  share HTTP + caching; kept `fetch_wind`'s observable behavior identical (verified by the
  untouched `test_fetch.py`). Shared CLI via `--metric wind/sun/both` (default `both`).

## Verified against real data (Boulder)
- Daylight 07:00–21:00, irradiance peaks ~13:00 (solar noon in MDT). Weak-sun daylight
  hours at the edges; monthly breakdown correctly shifts edges seasonally (winter
  09:00/17:00, summer 06:00/20:00). The clean bell curve shows in the by-hour table.

## Review loop
- The `code-reviewer` agent worked by name this session (registered after the earlier
  restart). Findings applied: run both metrics independently and return the worst exit code
  (a wind failure no longer hides the sun report); deduped `_with_time_parts` (import from
  analyze); unquoted a redundant annotation.
- **Privacy catch:** the reviewer flagged that `config.py`'s default location had been
  changed to real coordinates (user-set locally). Did NOT commit it — staged everything
  except config.py so the personal location stays local and the repo keeps the placeholder.
  Good reminder to diff `config.py` before every commit. [[plans-reflections-convention]]
