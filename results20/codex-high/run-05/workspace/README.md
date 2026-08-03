# Snake — a dependency-free terminal game

A classic Snake game that runs entirely in the terminal with Python's standard
library (`curses`) — no third-party packages needed.

## Run it

```bash
python3 -m snake_game
# or
./play_snake.py
```

Optional flags:

```bash
python3 -m snake_game --width 30 --height 20 --seed 42
```

- `--width`, `--height`: board size in cells (default `24 x 20`).
- `--seed`: a random seed for reproducible food placement.
- `--version`: print version and exit.

> `curses` needs a real terminal. If you see "This game needs a real
> terminal", make sure you're on a TTY and `TERM` is set (e.g. `export
> TERM=xterm`).

## Controls

| Key            | Action       |
| -------------- | ------------ |
| Arrow keys / W/A/S/D | Move |
| `Q`            | Quit         |

Eat the `@` food to grow and score one point. Hitting a wall or your own body
ends the game. Fill the board to win.

## Project layout

```
snake_game/
  __init__.py   package metadata
  logic.py      pure game rules (no UI) — easily unit-tested
  ui.py         curses rendering and input loop
  __main__.py   CLI entry point (arg parsing)
tests/
  test_logic.py unit tests for the game logic
play_snake.py   convenience launcher
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
