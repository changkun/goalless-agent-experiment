# Minesweeper

A small, dependency-free terminal Minesweeper written in Python 3.

## Run

```bash
python3 -m minesweeper
```

## How to play

- `r x y` — reveal the cell at column `x`, row `y`
- `f x y` — toggle a flag on that cell
- `q` / `quit` / `exit` — quit

Coordinates are 0-based. The first move is always safe (it's never a mine).

## Tests

```bash
python3 -m unittest minesweeper.test_game -v
```
