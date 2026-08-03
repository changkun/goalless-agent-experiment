# Terminal 2048

A dependency-free 2048 game playable in your terminal, written in pure Python.

## Play

```bash
python3 play2048.py          # or: python3 -m game2048
```

Controls:
- Arrow keys **or** `W`/`A`/`S`/`D` to move
- `q` / `ESC` to quit

The game ends when no moves remain; the board highlights green when you reach
2048 (or any target — the win banner appears whenever a tile hits 2048).

## Layout

- `game2048/core.py` — pure game logic (no I/O): board state, sliding/merging,
  scoring, spawn, game-over and win detection.
- `game2048/cli.py` — interactive terminal front end (raw-mode keyboard input,
  colored rendering).
- `game2048/__main__.py` — `python -m game2048` entry point.
- `tests/test_core.py` — unit tests for the engine.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

No third-party dependencies are required (never was; pytest is optional).
