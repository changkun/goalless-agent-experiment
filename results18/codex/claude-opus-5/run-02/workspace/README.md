# labyrinth

A dependency-free Python toolkit for generating, solving and rendering mazes in the terminal.

```
$ python3 -m labyrinth -H 5 -W 10 -s 7 -r box --longest
┌───────┬───────────┬───────────────────┐
│ ····· │ ········· │ ················· │
│ · ╷ · ╵ · ┌───┐ · │ · ┌───────┬───╴ · │
│ · │ ····· │ · │ · │ · │       │ ····· │
│ · └───────┤ · │ · ╵ · ├───╴   │ · ╶───┤
│ ········· │ · │ ····· │       │ ····· │
├───────────┘ · ├───────┤   ╶───┴───┐ · │
│ ············· │ ····· │ ······    │ · │
│ · ╶───────────┘ · ╷ · ╵ · ╷ · ╶───┘ · │
│ ················· │ ····· │ ········· │
└───────────────────┴───────┴───────────┘
```

## Usage

```
python3 -m labyrinth [-H ROWS] [-W COLS] [-a ALGORITHM] [-r STYLE]
                     [-s SEED] [--braid RATIO] [--solve | --longest] [--stats]
```

| Flag | Meaning |
| --- | --- |
| `-a/--algorithm` | `backtracker` (winding), `kruskal` (uniform), `prim` (bushy), `binary` (diagonal bias) |
| `-r/--render` | `blocks` (solid walls), `box` (box-drawing), `ascii` (`+---+`) |
| `-s/--seed` | reproducible output for the same seed and size |
| `--braid RATIO` | remove that fraction of dead ends, creating loops |
| `--solve` | mark the shortest path from the top-left to the bottom-right cell |
| `--longest` | mark the maze diameter (its longest shortest-path) |
| `--stats` | print cells, passages, dead ends, junctions, diameter, perfectness |

## Library

```python
import random
from labyrinth import recursive_backtracker, render_ascii, shortest_path, stats

maze = recursive_backtracker(10, 20, random.Random(1))
path = shortest_path(maze, (0, 0), (9, 19))
print(render_ascii(maze, path))
print(stats(maze))
```

- `labyrinth.grid.Grid` — cells as `(row, col)`, passages carved with `link`/`unlink`, queried with `linked`, `passages`, `has_wall`, `edges`.
- `labyrinth.generators` — the four carvers plus `braid` for loop creation; all take an optional `random.Random` for determinism.
- `labyrinth.solvers` — `flood` (BFS distances), `shortest_path` (A*), `longest_path`, `dead_ends`, `is_perfect`, `stats`.
- `labyrinth.render` — `render_blocks`, `render_box`, `render_ascii`, and the raw `wall_bitmap` if you want to draw your own.

Every generator produces a *perfect* maze (a spanning tree: exactly one path between any two cells) until you braid it.

## Tests

```
python3 -m unittest discover -s tests
```
