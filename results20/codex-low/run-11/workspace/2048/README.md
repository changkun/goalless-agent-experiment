# Terminal 2048

A dependency-free, terminal implementation of the classic 2048 sliding-tile
puzzle, written in pure Python with `curses`.

## Run it

```bash
python3 game.py
```

Requires Python 3 and a terminal that supports `curses` (Linux/macOS; on
Windows use WSL or Git Bash).

## Controls

| Key             | Action     |
| --------------- | ---------- |
| `WASD` / arrows | Move tiles |
| `u`             | Undo move  |
| `r`             | Restart    |
| `q`             | Quit       |

## How it plays

- Slide tiles with arrow/WASD keys; equal tiles merge into their sum.
- A new `2` (or sometimes `4`) appears after every move.
- Reach **2048** to win; the game ends when no moves are possible.
- Score tracks the current run, `Best` persists across restarts within a
  session, and undo rewinds individual moves.

## Files

- `game.py` — the whole game (board logic, rendering, input loop)
- `test_game.py` — headless sanity tests for the board logic
