# Game of Life

A tiny, dependency-free implementation of Conway's Game of Life in Python,
with a sparse (unbounded) board representation and a terminal animation CLI.

## Features

- `Board` is backed by a set of live-cell coordinates rather than a
  fixed-size array, so patterns can grow or shrink without worrying about
  running off the edge of a pre-allocated grid.
- Load patterns from simple ASCII art via `Board.from_pattern`.
- A handful of classic patterns are bundled in `gol/patterns.py`: `glider`,
  `lwss`, `pulsar`, `gun`.
- A terminal CLI animates a chosen pattern generation by generation.

## Usage

Run the animation directly with the standard library, no install required:

```bash
python3 -m gol.cli glider -g 60 -d 0.1
```

Options:

- `pattern` - one of `glider`, `lwss`, `pulsar`, `gun` (default: `glider`).
- `-g/--generations` - number of generations to simulate (default: `60`).
- `-d/--delay` - seconds to pause between generations (default: `0.1`).

You can also install the package to get a `gol` console script:

```bash
pip install -e .
gol pulsar -g 40
```

## Library usage

```python
from gol.board import Board

glider = Board.from_pattern(
    """
    .#.
    ..#
    ###
    """
)
next_gen = glider.step()
print(next_gen.render())
```

## Tests

Tests use only the standard library `unittest` module:

```bash
python3 -m unittest discover -s tests -v
```
