# maze.py — terminal maze generator & solver

A zero-dependency Python tool that generates and solves mazes right in the
terminal. No third-party packages required — just Python 3.

## Usage

```bash
# Random backtracker maze (default)
python3 maze.py

# Bigger maze with a specific random seed
python3 maze.py --width 25 --height 15 --seed 42

# Kruskal's algorithm with loops (braid = 40% of dead ends opened)
python3 maze.py --algorithm kruskal --braid 0.4

# Draw the solution path (A* by default, or BFS)
python3 maze.py --show-path
python3 maze.py --show-path --solver bfs
```

## Features

- **Generators**: recursive backtracker (depth-first) and Kruskal's algorithm
  (randomized spanning tree). Both produce perfect mazes (exactly one path
  between any two cells).
- **Braiding**: `--braid` opens a fraction of dead ends to create loops.
- **Solvers**: A* (Manhattan heuristic) and BFS. Both return the shortest path;
  A* samples fewer nodes on typical mazes.
- **Reproducible**: `--seed` makes any generated maze deterministic.
- **No dependencies**: works with stock Python.

## Library API

```python
import maze, random

grid = maze.generate_backtracker(20, 14, random.Random(1))
path = maze.solve_astar(grid, (0, 0), (19, 13))   # list of (x, y)
print(maze.render(grid, path=path))
```

The grid is a 2D list of bitmask integers where bit values encode open walls:

| Bit | Direction |
|-----|-----------|
| 1   | North     |
| 2   | East      |
| 4   | South     |
| 8   | West      |

## Validation

The included `--show-path` mode proves an A* route exists; run the internal
self-check (400 mazes across both algorithms plus braided variants) to confirm
every maze stays solvable.
