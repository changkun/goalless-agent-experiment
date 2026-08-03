# Terminal Minesweeper

A dependency-free Minesweeper that runs in your terminal, pure Python standard library.

## Run

```bash
python3 mine.py
```

## Play

- `0 0` — reveal the cell at row 0, column 0
- `f 0 0` — place / remove a flag at row 0, column 0
- `q` — quit

Reveal every non-mine cell to win. Hitting a mine ends the game.
The first reveal is always safe and positions the mines around it.
