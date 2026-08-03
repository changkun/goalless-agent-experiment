# Conway's Game of Life

A self-contained, zero-dependency implementation of John Conway's cellular
automaton in pure Python. Runs entirely in the terminal.

## Rules

On each generation:

- A live cell with **2 or 3** live neighbours survives.
- A dead cell with **exactly 3** live neighbours becomes alive.
- Everything else dies or stays dead.

## Quick start

```bash
# Print a pattern once (the default is the glider)
python3 cli.py glider

# Animate it in the terminal (replaces each frame in place)
python3 cli.py pulsar -n 60 --clear

# List available patterns
python3 cli.py nonexistent-on-purpose
```

## Command-line options

```
positional:
  pattern        which pattern to run (default: glider)

options:
  -n, --generations N   animate for N generations; omit to print once
  -d, --delay SEC       seconds between frames (default: 0.15)
  -c, --clear           redraw in place instead of scrolling (best in a TTY)
```

The animation uses a doubled-character layout so each cell reads as roughly
square on a normal terminal font.

## Patterns

| pattern | cells | behaviour                          |
|---------|-------|------------------------------------|
| glider  | 5     | travels diagonally, period 4       |
| blinker | 3     | simplest oscillator, period 2      |
| toad    | 6     | oscillator, period 2               |
| beacon  | 8     | oscillator, period 2               |
| pulsar  | 48    | period-3 oscillator                |
| gun     | 36    | Gosper glider gun, infinite growth |

## Project layout

- `life.py` — the grid engine (`Grid`) and the rules. No I/O; fully testable.
- `patterns.py` — the built-in patterns as plain `#`/`.` grids.
- `rle.py` — an RLE pattern loader plus small `period`/`is_gun` verifiers.
- `cli.py` — the terminal front-end.
- `test_life.py` — unit tests.

## Tests

```bash
python3 -m unittest test_life -v
```

The test suite cross-checks the fast engine against a slow, obviously-correct
reference implementation on 200 random grids, and mechanically verifies each
pattern's period and growth.

## Notes on the bounded grid

This is a finite grid; cells just outside the edge are treated as dead. This
means oscillators are given a dead margin in `patterns.py` so their
intermediate phases aren't clipped, and the glider gun needs a roomy grid to
show its growth. On an infinite grid these patterns behave canonically.
