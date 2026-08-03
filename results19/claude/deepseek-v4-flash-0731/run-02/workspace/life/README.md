# life

Conway's Game of Life — a minimal, dependency-free terminal implementation in a single
Python file.

## Run

```bash
python3 game.py            # random soup, auto-sizing to the terminal
python3 game.py 100 40     # exact grid size (width x height)
python3 game.py --glider   # start from a glider pattern instead of a random soup
```

## Controls (interactive terminal)

| Key    | Action          |
|--------|-----------------|
| Space  | pause / resume |
| r      | reseed random  |
| c      | clear board     |
| q      | quit            |

Nearly all of the logic lives in `evolve()` — a board is just a `set` of `(col, row)`
live-cell coordinates, so each generation is a couple of scalar passes. No ANSI escapes
contaminate the payload either; rendering is plain characters.
