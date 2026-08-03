# Conway's Game of Life (terminal)

A polished, zero-dependency Conway's Game of Life that runs in your terminal.
Pure Python stdlib — no pip installs, no GUI.

## Run

```bash
python3 game_of_life.py                 # glider
python3 game_of_life.py --pattern gosper   # glider gun
python3 game_of_life.py --random           # random soup
```

## Features

- **Toroidal universe** — cells wrap around all four edges.
- **Heat coloring** — cells brighten as they age (young = dim gray → mature = yellow).
- **Classic patterns** — glider, blinker, toad, beacon, pulsar, and the Gosper glider gun.
- **Live HUD** — generation, population, fps, and running/paused state.
- **Zero dependencies** — only the standard library.

## Controls

| Key    | Action                                  |
|--------|-----------------------------------------|
| `space`| pause / resume                          |
| `n`    | advance one generation (while paused)   |
| `c`    | clear the board                         |
| `r`    | random board (~30% density)             |
| `v`    | inject a "virus" (random live cells)    |
| `s`/`l`| save / load the board to/from a file    |
| `[`/`]`| slower / faster                         |
| `h`    | toggle HUD                              |
| `?`    | help                                    |
| `q`    | quit                                    |

## Options

```
--pattern {glider,blinker,toad,beacon,pulsar,gosper}
--rows N  --cols N   grid size (each cell = 2 chars wide)
--fps N              generations per second (default 8)
--random             start with a random board instead of a pattern
--density F          density for random boards (default 0.30)
--load PATH          file to load at startup
```

## Design notes

- `Board` stores each live cell as a timestamp (alive-age), which drives both
  heat coloring and quick survival checks (any nonzero = alive).
- The main loop is deliberately simple: clear screen → draw → poll a key with a
  non-blocking read → step. Raw-mode key reading uses `termios`/`select` on POSIX,
  with a line-based fallback elsewhere.
