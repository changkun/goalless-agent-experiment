# Terminal Minesweeper

A small, dependency-free Minesweeper game you can play in your terminal.

## Install

No dependencies. Requires Python 3.8+.

```bash
pip install -e .   # optional
python -m minesweeper.cli
```

## Usage

```bash
python -m minesweeper.cli                  # 9x9, 10 mines (classic)
python -m minesweeper.cli --rows 16 --cols 16 --mines 40
```

Commands inside the game:

- `r <row> <col>` — reveal a cell
- `f <row> <col>` — flag / unflag a cell
- `q` — quit

Revealing a mine loses; revealing every safe cell wins.

## Run the tests

```bash
python -m unittest discover minesweeper/tests
```
