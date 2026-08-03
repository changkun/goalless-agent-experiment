# Snake

A minimal terminal Snake game in pure Python (stdlib only).

## Features
- Pure, testable game-logic core (`snake_game/core.py`) decoupled from the UI.
- Curses-based terminal interface.
- `WASD` / arrow-key controls, pause, restart, and a simple greedy AI helper.
- Deterministic with a `--seed` option for testing/replay.

## Run
```bash
python3 -m snake_game                 # default 20x10 board
python3 -m snake_game --width 30 --height 20
```

## Controls
- Arrows or `WASD`: steer
- `p`: pause / resume
- `r`: restart (after a game over / win)
- `q`: quit

## Test
```bash
python3 -m unittest discover -s tests
```

## Layout
- `snake_game/core.py` — game state, movement, collision, food, and AI.
- `snake_game/ui.py` — curses rendering and input loop.
- `snake_game/__main__.py` — CLI entry point.
- `tests/test_core.py` — unit tests for the logic core.
