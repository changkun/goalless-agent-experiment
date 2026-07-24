"""Maze carving algorithms.

Every generator returns a :class:`~labyrinth.grid.Grid` that is a *perfect*
maze: exactly one path between any two cells, i.e. a spanning tree of the grid
graph. ``braid`` can afterwards knock out dead ends to create loops.
"""

from __future__ import annotations

import random
from typing import Callable

from .grid import Cell, Grid


def recursive_backtracker(height: int, width: int, rng: random.Random | None = None) -> Grid:
    """Depth-first carving: long, winding corridors with few junctions."""
    rng = rng or random.Random()
    grid = Grid(height, width)
    start = (rng.randrange(height), rng.randrange(width))
    visited = {start}
    stack = [start]
    while stack:
        current = stack[-1]
        unvisited = [n for n in grid.neighbors(current) if n not in visited]
        if not unvisited:
            stack.pop()
            continue
        nxt = rng.choice(unvisited)
        grid.link(current, nxt)
        visited.add(nxt)
        stack.append(nxt)
    return grid


def randomized_kruskal(height: int, width: int, rng: random.Random | None = None) -> Grid:
    """Union-find over shuffled walls: uniform texture, many short dead ends."""
    rng = rng or random.Random()
    grid = Grid(height, width)
    parent: dict[Cell, Cell] = {cell: cell for cell in grid.cells()}

    def find(cell: Cell) -> Cell:
        root = cell
        while parent[root] != root:
            root = parent[root]
        while parent[cell] != root:
            parent[cell], cell = root, parent[cell]
        return root

    walls: list[tuple[Cell, Cell]] = []
    for cell in grid.cells():
        row, col = cell
        for other in ((row + 1, col), (row, col + 1)):
            if grid.contains(other):
                walls.append((cell, other))
    rng.shuffle(walls)

    for a, b in walls:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            grid.link(a, b)
    return grid


def randomized_prim(height: int, width: int, rng: random.Random | None = None) -> Grid:
    """Frontier growth from a seed cell: bushy mazes with lots of branching."""
    rng = rng or random.Random()
    grid = Grid(height, width)
    start = (rng.randrange(height), rng.randrange(width))
    visited = {start}
    frontier = [(start, n) for n in grid.neighbors(start)]
    while frontier:
        index = rng.randrange(len(frontier))
        inside, outside = frontier.pop(index)
        if outside in visited:
            continue
        grid.link(inside, outside)
        visited.add(outside)
        frontier.extend(
            (outside, n) for n in grid.neighbors(outside) if n not in visited
        )
    return grid


def binary_tree(height: int, width: int, rng: random.Random | None = None) -> Grid:
    """Carve north or east from each cell: a strong diagonal bias, very fast."""
    rng = rng or random.Random()
    grid = Grid(height, width)
    for cell in grid.cells():
        row, col = cell
        options = []
        if row > 0:
            options.append((row - 1, col))
        if col + 1 < width:
            options.append((row, col + 1))
        if options:
            grid.link(cell, rng.choice(options))
    return grid


def braid(grid: Grid, rng: random.Random | None = None, ratio: float = 1.0) -> Grid:
    """Remove ``ratio`` of dead ends in place, creating loops.

    A dead end has exactly one passage; it is joined to a random neighbor it is
    not already linked to (preferring another dead end, which keeps corridors
    from becoming too open).
    """
    if not 0.0 <= ratio <= 1.0:
        raise ValueError("ratio must be between 0 and 1")
    rng = rng or random.Random()
    dead_ends = [cell for cell in grid.cells() if len(grid.passages(cell)) == 1]
    rng.shuffle(dead_ends)
    for cell in dead_ends[: round(len(dead_ends) * ratio)]:
        if len(grid.passages(cell)) != 1:
            continue
        candidates = [n for n in grid.neighbors(cell) if not grid.linked(cell, n)]
        if not candidates:
            continue
        best = [n for n in candidates if len(grid.passages(n)) == 1] or candidates
        grid.link(cell, rng.choice(best))
    return grid


GENERATORS: dict[str, Callable[..., Grid]] = {
    "backtracker": recursive_backtracker,
    "kruskal": randomized_kruskal,
    "prim": randomized_prim,
    "binary": binary_tree,
}
