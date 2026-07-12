# Game of Life

A tiny, dependency-free implementation of Conway's Game of Life, with a
sparse (unbounded) grid representation and a terminal animator.

## Usage

Run the animator directly from the source tree:

```bash
python -m gameoflife.cli --preset glider --generations 60
```

Or, after installing (`pip install -e .`), use the console script:

```bash
gameoflife --preset pulsar --generations 30 --interval 0.1
```

You can also supply your own pattern file, where `#` marks a living cell:

```
.#.
..#
###
```

```bash
gameoflife --file my_pattern.txt
```

## Library usage

```python
from gameoflife import Board

board = Board({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)})  # glider
next_gen = board.step()
print(next_gen.render())
```

## Running tests

```bash
pip install pytest
pytest
```
