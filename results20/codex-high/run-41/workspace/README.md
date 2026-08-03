# Terminal Minesweeper

A self-contained, zero-dependency Minesweeper game for the terminal, written in Python.

## Run

```bash
python3 -m minesweeper.game
```

## How to play

- `r <row> <col>` — reveal a cell
- `f <row> <col>` — place / remove a flag
- `q` — quit

The first reveal is always safe: mines are placed only after your first click,
and never under the clicked cell or its neighbors.

## Difficulties

| Level        | Board   | Mines |
|--------------|---------|-------|
| Beginner     | 9x9     | 10    |
| Intermediate | 16x16   | 40    |
| Expert       | 16x30   | 99    |

## Features

- Flood-fill reveals empty regions automatically
- Safe first move
- Flagging and a live mine counter
- Win / loss detection with a restart loop

## Tests

```bash
python3 /tmp/test_minesweeper.py
```
