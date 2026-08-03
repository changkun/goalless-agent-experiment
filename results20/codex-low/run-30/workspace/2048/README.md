# 2048

A dependency-free 2048 game that runs in your terminal, written in pure Python
(stdlib only). It has a clean, fully unit-tested game engine and a small
interactive TUI.

```
  score: 412     moves: 38
  ┌────────┐
  │  ·  2  4  ·│
  │ 16  2  8 16│
  │  · 32  4  ·│
  │  2  8  · 64│
  └────────┘
```

## Play

```bash
cd 2048
python3 main.py            # interactive 4x4 game
python3 main.py --size 3   # smaller board
python3 main.py --text ddaa  # scripted mode (wasd), prints the board
```

Controls in interactive mode:

| Key | Action |
| --- | --- |
| Arrow keys / `hjkl` | Move tiles |
| `n` | New game |
| `q` | Quit |

The board uses ANSI colors for different tile values. Interactive mode requires
a TTY; the `--text` flag works anywhere.

## Layout

```
2048/
  engine/
    core.py     # Game engine: board, moves, scoring, win/lose detection
    __init__.py
  main.py       # terminal UI + CLI entry point
  tests/
    test_engine.py
  README.md
```

## Engine

The engine lives in `engine/core.py` and is intentionally independent of the
UI so it is easy to test or reuse:

```python
from engine.core import Game, Move

game = Game(size=4, seed=1)   # seed for reproducibility
result = game.move(Move.LEFT) # returns a move result
game.score                     # current score
game.is_game_over()            # True when no move can change the board
```

Core rules implemented:

- Each move pushes all tiles in that direction, merging equal neighbors **once**
  (chains like `[2,2,2,2]` become `[4,4]`, not `[8]`).
- Every move that changes the board spawns a new `2` (90%) or `4` (10%) tile in
  a random empty cell.
- Score accumulates the value of each merged tile.
- Reaching `2048` sets the `won` flag (you can keep playing past it).
- `is_game_over()` is `True` only when no move in any direction changes the
  board.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite covers tile merging in all four directions, single-merge semantics,
scoring, tile spawning, win detection, game-over detection, input validation,
and seeded reproducibility.
