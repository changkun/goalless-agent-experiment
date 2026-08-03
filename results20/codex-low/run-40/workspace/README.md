# Minesweeper

A classic Minesweeper game you can play right in your terminal, written in
pure Python with no dependencies.

## Run

```bash
python3 -m minesweeper
```

Customize the board:

```bash
python3 -m minesweeper -r 16 -c 16 -m 40     # bigger board
python3 -m minesweeper --seed 42             # reproducible board
```

## Commands

- `reveal <cell>` / `r <cell>` — reveal a cell (first move is always safe)
- `flag <cell>` / `f <cell>` — toggle a flag
- `quit` / `q` — exit

Cells are zero-indexed with index `row * cols + col`.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Layout

- `minesweeper/game.py` — core board engine (mines, counts, flood-fill reveal)
- `minesweeper/cli.py` — terminal interface
- `tests/test_game.py` — unit tests for the engine
