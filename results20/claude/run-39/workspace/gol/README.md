# Game of Life

A small, dependency-free implementation of Conway's Game of Life in pure
Python (standard library only).

## Files

| File          | Purpose                                              |
|---------------|------------------------------------------------------|
| `engine.py`   | The simulation engine (`step`), using a sparse set of live cells |
| `patterns.py` | Classic patterns (still lifes, oscillators, spaceships, a gun)  |
| `render.py`   | Terminal rendering                                    |
| `animate.py`  | Live terminal animation                              |
| `gallery.py`  | Print every pattern in its own box                   |
| `test_gol.py` | Test suite (engine + pattern verification)           |

## Running

```console
$ python3 animate.py            # live animation of the Gosper gun
$ python3 animate.py glider 60 30 20
$ python3 gallery.py            # all patterns as ASCII art
$ python3 test_gol.py           # run the tests
$ python3 -m pytest gol         # ...or under pytest, if installed
```

## Design notes

- The universe is **unbounded**: only live cells are stored in memory, so
  the representation is proportional to the population, not a bounding box.
- One generation is computed with a single counting pass over each cell's
  8 neighbours (via `collections.Counter`).
- The engine (`engine.py`) is pure and side-effect free, so the tests and any
  alternative frontend (PNG, web, ...) can reuse it directly.
