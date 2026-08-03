# Conway's Game of Life

An interactive [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
implementation for the terminal, built with Python's `curses` module.

## Requirements

- Python 3.7+ (uses `dict` typing syntax and `: dict[]` annotations from 3.9+; runs on 3.9+)
- A terminal that supports curses (Linux/macOS; on Windows use Windows Terminal with WSL)

## Run

```bash
python3 life.py            # start with a random board
python3 life.py --seed 42  # reproducible random board
```

## Controls

| Key        | Action                  |
|------------|-------------------------|
| `space`    | pause / resume          |
| `r`        | randomize the board     |
| `c`        | clear the board         |
| `+` / `=`  | speed up                |
| `-` / `_`  | slow down               |
| `q`        | quit                    |

## Rules

Each cell has two states — alive (`#`) or dead. At each generation:

1. A live cell with 2 or 3 neighbors survives.
2. A dead cell with exactly 3 neighbors becomes alive.
3. All other cells die or stay dead.

Stars, oscillators, and gliders emerge naturally from random seeds.
