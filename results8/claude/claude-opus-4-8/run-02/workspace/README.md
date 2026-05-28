# maze.py

A self-contained terminal maze generator and solver, animated.

- **Generate** with a recursive backtracker (depth-first carving) — long, windy corridors.
- **Solve** with breadth-first search — watch the frontier flood outward, then the
  shortest path light up in gold.

No dependencies beyond the Python 3 standard library.

## Usage

```bash
python3 maze.py [width] [height] [--seed N] [--fast]
```

- `width` / `height` — maze size in cells (default 28×14). The drawn grid is ~2× this.
- `--seed N` — reproducible maze.
- `--fast` — skip the animation delay (renders as fast as the terminal allows).

### Examples

```bash
python3 maze.py                 # default 28×14, animated
python3 maze.py 40 20           # bigger
python3 maze.py 20 10 --seed 7  # reproducible
python3 maze.py 30 15 --fast    # no delay
```

## Legend

| Glyph | Meaning                         |
|-------|---------------------------------|
| `█`   | wall                            |
| `·`   | freshly carved corridor (green) |
| `•`   | BFS frontier — visited (cyan)   |
| `◆`   | shortest path (gold)            |

Best viewed in a terminal that supports 256 colours. The maze runs from the
top-left corner to the bottom-right.
