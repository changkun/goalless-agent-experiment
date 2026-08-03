# Terminal Snake 🐍

A classic Snake game that runs entirely in the terminal using Python's
standard-library `curses` module — zero dependencies required.

## Run it

```bash
python3 snake_game/snake.py
```

## Controls

| Action        | Keys                          |
|---------------|-------------------------------|
| Move          | Arrow keys or `W` `A` `S` `D` |
| Restart round | `R`                           |
| Quit          | `Q`                           |

## Rules

- Eat the red `*` to grow and score a point.
- Don't hit the wall or your own tail.
- The game ends on a collision; press `R` to play again or `Q` to quit.

Nice terminal with color support recommended for the full look.
