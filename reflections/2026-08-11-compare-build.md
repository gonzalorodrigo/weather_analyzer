# Reflections — 2026-08-11 (wind vs sun comparison)

Adding a `compare` mode overlaying wind and sun per hour.

## Design
- The payoff of comparing the two signals is the **combined recommendation**: normalize
  wind and radiation each to [0,1] over the **daylight hours only**, sum, take the lowest.
  Normalizing over the daylight subset (not full 24h) keeps the score meaningful for
  watering and avoids night wind skewing it. Restricting to daylight (via
  `solar.daylight_hours`) guarantees the pick is an actual daytime slot.
- Dual y-axes for the overlay chart because wind (km/h) and radiation (W/m²) have different
  scales — a single axis would flatten one of them.

## Verified (user's location)
- Best watering hours came out **07:00–09:00**: calm wind (8.5–9.2 km/h) while the sun is
  still weak (11–174 W/m² vs the ~692 midday peak). Matches the earlier by-hand read of the
  separate wind and sun reports.

## Process
- `code-reviewer` returned **clean, no findings** this round — the `_normalize` guards
  (NaN / flat series) and daylight restriction held up under scrutiny.
- Same `config.py` privacy step as last time: staged everything **except** config.py so the
  real coordinates stay local. Diff config.py before every commit. [[plans-reflections-convention]]
