"""Maze / terrain generators.

Every generator returns a :class:`~pathviz.grid.Grid` whose ``start`` is the
top-left floor cell and whose ``goal`` is the bottom-right floor cell. Passing a
``seed`` makes generation deterministic.
"""

from __future__ import annotations

import random

from pathviz.grid import Cell, Grid

GENERATORS = ("backtracker", "prim", "rooms")

#: Terrain cost tiers used when weighted generation is requested.
WEIGHT_TIERS = (1, 1, 1, 2, 3, 5)


def generate(
    width: int,
    height: int,
    kind: str = "backtracker",
    seed: int | None = None,
    weighted: bool = False,
) -> Grid:
    """Build a grid of ``width`` x ``height`` cells using generator ``kind``."""
    if kind not in GENERATORS:
        raise ValueError(f"unknown generator {kind!r}; expected one of {GENERATORS}")
    rng = random.Random(seed)
    width, height = _odd(width), _odd(height)
    grid = Grid(width, height)

    if kind == "backtracker":
        _backtracker(grid, rng)
    elif kind == "prim":
        _prim(grid, rng)
    else:
        _rooms(grid, rng)

    if weighted:
        _apply_weights(grid, rng)

    grid.start = _corner_floor(grid, from_end=False)
    grid.goal = _corner_floor(grid, from_end=True)
    return grid


def _odd(value: int) -> int:
    """Mazes need odd dimensions so walls and cells alternate cleanly."""
    if value < 3:
        return 3
    return value if value % 2 else value - 1


def _backtracker(grid: Grid, rng: random.Random) -> None:
    """Randomized depth-first search: long winding corridors, few junctions."""
    start = (1, 1)
    grid.carve(start)
    stack = [start]
    while stack:
        cell = stack[-1]
        options = [n for n in _wall_jumps(grid, cell) if not grid.is_floor(n)]
        if not options:
            stack.pop()
            continue
        nxt = rng.choice(options)
        _carve_between(grid, cell, nxt)
        stack.append(nxt)


def _prim(grid: Grid, rng: random.Random) -> None:
    """Randomized Prim's algorithm: bushier mazes with many short branches."""
    start = (1, 1)
    grid.carve(start)
    frontier = [(start, n) for n in _wall_jumps(grid, start)]
    while frontier:
        index = rng.randrange(len(frontier))
        cell, nxt = frontier.pop(index)
        if grid.is_floor(nxt):
            continue
        _carve_between(grid, cell, nxt)
        frontier.extend((nxt, n) for n in _wall_jumps(grid, nxt) if not grid.is_floor(n))


def _rooms(grid: Grid, rng: random.Random) -> None:
    """Open field with scattered wall blobs, so many routes exist."""
    for y in range(1, grid.height - 1):
        for x in range(1, grid.width - 1):
            grid.carve((x, y))
    blobs = max(1, (grid.width * grid.height) // 40)
    for _ in range(blobs):
        x = rng.randrange(1, grid.width - 1)
        y = rng.randrange(1, grid.height - 1)
        for dx in range(rng.randint(1, 3)):
            for dy in range(rng.randint(1, 3)):
                cell = (x + dx, y + dy)
                if _is_interior(grid, cell):
                    grid.cells[cell[1]][cell[0]] = 0
    grid.carve((1, 1))
    grid.carve((grid.width - 2, grid.height - 2))


def _apply_weights(grid: Grid, rng: random.Random) -> None:
    """Sprinkle patches of expensive terrain across the floor."""
    patches = max(2, (grid.width * grid.height) // 30)
    for _ in range(patches):
        cost = rng.choice(WEIGHT_TIERS)
        cx = rng.randrange(grid.width)
        cy = rng.randrange(grid.height)
        radius = rng.randint(1, 3)
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                cell = (x, y)
                if grid.is_floor(cell) and abs(x - cx) + abs(y - cy) <= radius:
                    grid.set_weight(cell, cost)


def _wall_jumps(grid: Grid, cell: Cell) -> list[Cell]:
    """Cells two steps away, i.e. reachable by knocking out one wall."""
    x, y = cell
    candidates = ((x, y - 2), (x + 2, y), (x, y + 2), (x - 2, y))
    return [c for c in candidates if _is_interior(grid, c)]


def _carve_between(grid: Grid, a: Cell, b: Cell) -> None:
    grid.carve(b)
    grid.carve(((a[0] + b[0]) // 2, (a[1] + b[1]) // 2))


def _is_interior(grid: Grid, cell: Cell) -> bool:
    x, y = cell
    return 1 <= x < grid.width - 1 and 1 <= y < grid.height - 1


def _corner_floor(grid: Grid, from_end: bool) -> Cell:
    """Floor cell closest to a corner, measured by Manhattan distance."""
    corner = (grid.width - 1, grid.height - 1) if from_end else (0, 0)
    return min(
        grid.floors(),
        key=lambda c: (abs(c[0] - corner[0]) + abs(c[1] - corner[1]), c),
    )
