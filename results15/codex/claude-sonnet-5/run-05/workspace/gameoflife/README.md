# Game of Life

A small, dependency-free terminal implementation of Conway's Game of Life.

## Usage

```bash
python -m gameoflife.cli --pattern glider --generations 40 --interval 0.1
```

Available patterns: `glider`, `blinker`, `toad`, `beacon`, `pulsar`,
`gosper-glider-gun`.

Run `python -m gameoflife.cli --help` for all options.

## Development

Run the test suite (stdlib only, no dependencies needed):

```bash
python -m unittest discover -s tests -v
```

## Library usage

```python
from gameoflife import Board

board = Board.from_pattern([".#.", "..#", "###"])
board = board.step()
print(board.render())
```
