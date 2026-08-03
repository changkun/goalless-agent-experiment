# Game of Life

A tiny, dependency-free Conway's Game of Life in Python. Cells live on an
infinite grid backed by a set of live coordinates.

## Usage

Run via the module (no install needed):

```bash
python3 -m game_of_life.cli            # default: blinker, 5 generations
python3 -m game_of_life.cli glider -n 20
python3 -m game_of_life.cli gosper -n 10
python3 -m game_of_life.cli -i 0.1 blinker -n 30
```

Or pip-install it to get the `game-of-life` command:

```bash
pip install -e .
game-of-life gosper -n 10
```

The `pattern` argument accepts either a built-in name
(`block`, `blinker`, `glider`, `gosper`) or a raw RLE body, e.g.
`2o$2o!`.

## Library API

```python
from game_of_life import Board

b = Board()
b.toggle(0, 0)
b.toggle(1, 0)
b.toggle(2, 0)
b.step()          # advance one generation
b.population()
```

Also available: `load_pattern`, `parse_rle`, `get_board`, and the
`game_of_life.render` module for text output.

## Tests

```bash
python3 -m unittest discover -s tests
```
