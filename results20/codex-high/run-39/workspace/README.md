# maze

A tiny, dependency-free terminal maze generator and solver.

## How it works

- **Generation** uses recursive backtracking (iterative DFS) to carve a
  *perfect* maze — exactly one path between every pair of cells.
- **Solving** runs an iterative depth-first search from start to end.
- **Rendering** maps cell walls onto a character lattice (`#` for walls).

## Usage

```bash
python -m maze              # 12x12 maze + path length
python -m maze 8 5          # custom size (rows cols)
python -m maze --seed 42     # reproducible maze
python -m maze --solution   # show the solved maze with the path marked
python -m maze --animate    # animate the solver walking the maze
```

Run directly from source (no install needed):

```bash
PYTHONPATH=. python -m maze --seed 42
```

Or install as a CLI:

```bash
pip install -e .
maze --animate
```
