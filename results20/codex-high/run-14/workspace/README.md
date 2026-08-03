# Game of Life

A zero-dependency implementation of Conway's Game of Life in pure Python.

## Usage

Run the CLI animation:

```bash
python -m life
```

Options:

```bash
python -m life --pattern pulsar            # classic preselected pattern
python -m life --random --density 0.35     # random soup
python -m life --wrap --generations 200    # toroidal board, more generations
python -m life --single --pattern block     # print one static frame
```

Available preset patterns: `blinker`, `block`, `glider`, `pulsar`.

## Library

```python
from life import Game

game = Game(width=40, height=20)
game.load("glider")
for _ in range(100):
    game.step()
print(game.board())
```

## Tests

```bash
python -m unittest discover tests -v
```
