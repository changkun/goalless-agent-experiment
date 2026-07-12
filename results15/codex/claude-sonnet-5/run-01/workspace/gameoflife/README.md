# Game of Life

A tiny, dependency-free implementation of Conway's Game of Life, with an
infinite sparse-grid engine and a terminal animation CLI.

## Usage

Run a pattern directly from the repo root:

```bash
python3 -m gameoflife.cli glider
```

Options:

```
usage: cli.py [-h] [-g GENERATIONS] [-d DELAY]
               [{beacon,blinker,glider,lightweight_spaceship,pulsar,toad}]

positional arguments:
  {beacon,blinker,glider,lightweight_spaceship,pulsar,toad}
                        Starting pattern to animate (default: glider).

options:
  -h, --help            show this help message and exit
  -g GENERATIONS, --generations GENERATIONS
                        Number of generations to simulate (default: 60).
  -d DELAY, --delay DELAY
                        Seconds to pause between generations (default: 0.1).
```

Example:

```bash
python3 -m gameoflife.cli pulsar -g 100 -d 0.08
```

## Design

- `gameoflife/engine.py` — `Board` stores only live cells as a set of
  `(x, y)` tuples, so the grid is effectively infinite; gliders and
  spaceships can wander without any bounds bookkeeping.
- `gameoflife/patterns.py` — a small library of classic patterns
  (still lifes, oscillators, spaceships).
- `gameoflife/cli.py` — renders the board into the terminal window each
  generation, centering the starting pattern automatically.

## Tests

No third-party dependencies are required; tests use the standard library's
`unittest`:

```bash
python3 -m unittest discover -s tests -v
```
