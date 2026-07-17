# life — Conway's Game of Life in your terminal

A zero-dependency Python 3 program. The universe is a torus (edges wrap),
live cells age, and each cell's glyph and color show its age — newborns are
dim `·`, ancients burn bright `@` (or `█`, depending on palette).

## Run it

```sh
python3 life.py                      # random soup, 12 gen/s
python3 life.py --pattern pulsar
python3 life.py --pattern acorn --speed 30 --palette 1
python3 life.py --density 0.3 --seed 99
```

## Controls

| key | action |
|-----|--------|
| `space` | pause / resume |
| `.` | step one generation (while paused) |
| `,` | step backward (up to 200 gens of history) |
| `+` / `-` | speed up / slow down |
| `p` | cycle palette (classic / embers / binary) |
| `r` | reseed |
| `1`–`8` | jump to a pattern: glider, r-pentomino, acorn, blinker, pulsar, lwss, block |
| `h` | toggle help in the HUD |
| `q` / `esc` | quit |

The window resizes live — the universe rebuilds to fit.

## Headless modes (no terminal needed)

```sh
python3 life.py --check                          # engine self-test
python3 life.py --snapshot 100 --seed 7          # evolve 100 gens, print ASCII
python3 life.py --snapshot 30 --pattern acorn --cols 80 --rows 30
python3 tui_smoke.py                             # drive the real TUI in a pty
```

`--snapshot` prints the grid as text plus a 16-hex-char fingerprint
(SHA-256 of the rendering), so runs are comparable and verifiable:
same seed + same flags ⇒ same fingerprint, always.

## How it works

The universe is a `dict[(x,y) → age]` of live cells; each tick counts
neighbors with a single pass of dictionary increments (B3/S23 rules), so
cost scales with live cells, not grid area. The renderer diffs nothing — it
repaints each frame with 24-bit ANSI colors, cursor-homed, one write per
frame. Colors interpolate from a "born" color to an "old" color with a soft
exponential knee, so you can watch heat flow out of an explosion.
