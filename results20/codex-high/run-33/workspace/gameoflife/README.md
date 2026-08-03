# Terminal Game of Life

A tiny, dependency-free implementation of Conway's Game of Life with an
interactive `curses` UI. The world is an **unbounded, sparse grid** — only live
cells and their neighbours are ever computed, so it never runs out of edges.

Built with the Python standard library only (`curses`, `unittest`).

## Quick start

```bash
python3 -m gameoflife
```

or, once installed:

```bash
pip install -e .
gameoflife
```

## Controls

| Key | Action |
| --- | --- |
| `Space` | pause / resume |
| `s` | step one generation |
| `n` / `p` | next / previous pattern |
| `c` | clear the grid |
| `Enter` | toggle cell under the × cursor |
| `+` / `-` | speed up / slow down |
| `o` | centre the pattern in the view |
| arrows | pan the view |
| `r` | reset the view origin |
| `q` | quit |

## Patterns

Includes 15 classic patterns: glider, Gosper glider gun, pulsar, R-pentomino,
acorn, diehard, blinker, beacon, toad, block, pi-heptomino, and the three
spaceships (LWSS / MWSS / HWSS).

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Layout

- `engine.py` — the sparse `World` simulation
- `patterns.py` — ASCII-art pattern definitions and loader
- `ui.py` — the curses interactive interface
