# SNEK

A tiny retro Snake game for the terminal, written in pure Python (standard
library only — no dependencies).

## Run

```bash
python3 snake/snake.py
```

## Controls

- Move: arrow keys or `h`/`j`/`k`/`l`
- Pause: `P` or `Space`
- Quit to menu: `Q`

## How it works

- Speeds up as you eat — every 4 pieces the snake moves a bit faster.
- Scores persist across sessions in a per-user file
  (`~/.snek_scores.txt` by default), so it works without special privileges.
- Top 5 personal bests are shown on the High Scores screen.
