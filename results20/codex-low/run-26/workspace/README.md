# starfield

A tiny, zero-dependency Python tool that prints a random ASCII night sky.

## Usage

Run it as a module (no install required):

```bash
python3 -m starfield          # 80x24 default
python3 -m starfield 60 12    # custom width/height
python3 -m starfield 60 12 --density 0.4
python3 -m starfield 60 12 --seed 42   # reproducible output
python3 -m starfield --full-block       # single-character render
```

Example output:

```
.....*........o....*..#..........*......
..........#........#.*.*..oO......o*..*.
...o........*....*....+.........*.......
```

## Library

```python
from starfield.generator import generate

rows = generate(60, 12, density=0.18, seed=1234)
print("\n".join(rows))
```

- `width`, `height` — grid dimensions in characters.
- `density` — probability any given cell holds a star (`0.0`–`1.0`).
- `palette` — ordered characters from faintest to brightest; the first entry
  marks empty cells. Defaults to `(".", "*", "+", "o", "O", "*", "#", "@")`.
- `seed` — optional RNG seed for reproducible output.

Bright stars are intentionally rarer than faint ones for a natural look.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
