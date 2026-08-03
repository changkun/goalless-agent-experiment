# Ember — Focus Timer

A calm, self-contained Pomodoro focus timer that runs entirely in the browser.
**No dependencies, no build step, no network** — just open `index.html` and work.

## Features

- **Pomodoro timer** — Focus / Short break / Long break modes, with configurable
  durations, a circular progress ring, and a daily-goal pip tracker per cycle.
- **Ambient soundscapes** — Rain, brown noise, crickets, and fire, synthesized
  live with the Web Audio API. No audio files; nothing is downloaded.
- **Statistics dashboard** — records every completed focus session locally and
  renders a 16-week GitHub-style heatmap plus a 7-day bar chart, session count,
  total focus minutes, and current day streak.
- **Keyboard shortcuts** — `space` start/pause · `r` reset · `n` stats ·
  `m` next mode · `s` cycle ambience.
- **Privacy** — all data lives in `localStorage` on your machine. Nothing is
  uploaded anywhere.

## Run it

```bash
# just open it
open index.html          # macOS
xdg-open index.html      # Linux
# or serve it if you prefer
python3 -m http.server 8080   # then visit http://localhost:8080
```

## How the sound is made (no files)

Each ambience is a small graph of Web Audio nodes built on demand:

| Sound | Recipe |
|-------|--------|
| Rain   | pink-noise bed through low-pass + high-pass filters, overlaid with sparse high-frequency droplet oscillator pings |
| Brown  | brown-noise through a low-pass filter for a warm, ocean-like rumble |
| Crickets | periodic 4–5.5 kHz oscillator chirps with a rising pitch bend |
| Fire   | brown-noise through a band-pass filter, plus occasional square-wave "crackle" pops |

Only one ambience plays at a time; activating a new one crossfades out the
previous and crossfades in the new (`setTargetAtTime`).

## Keyboard map

| Key | Action |
|-----|--------|
| `space` | start / pause |
| `r` | reset current session (and cycle) |
| `n` | toggle statistics |
| `m` | cycle focus → short → long |
| `s` | cycle ambience on/off |

## Notes

- The stats heatmap uses a validated sequential blue ramp (monotonic lightness,
  dark-surface selected). See the dataviz skill's palette for the full set.
- Sessions are kept for a rolling 30-day window.
