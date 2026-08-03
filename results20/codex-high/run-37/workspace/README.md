# Terminal Snake

A small, dependency-free Snake game that runs in your terminal using Python's
standard library (`curses`). No pip installs, no external dependencies.

## How to run

```bash
python3 run.py
```

Or as a module:

```bash
python3 -m snake_game
```

## How to play

- Use the **arrow keys** to steer the snake.
- Eat the red `@` food to grow and score points.
- The game speeds up as your score climbs.
- Avoid walls and your own tail.
- Press **Q** any time to quit a round.

Scores are saved to `snake_game/highscores.txt` and shown on the high-score
screen from the main menu.

## Files

- `snake_game/game.py` — game logic and rendering
- `run.py` — thin entry point
- `README.md` — this file

## Requirements

- A terminal that supports `curses` (Linux/macOS/Windows Terminal with WSL).
