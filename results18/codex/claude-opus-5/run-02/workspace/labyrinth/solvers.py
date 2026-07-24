"""Path finding and analysis over a carved grid."""

from __future__ import annotations

import heapq
from collections import deque

from .grid import Cell, Grid


def flood(grid: Grid, start: Cell) -> dict[Cell, int]:
    """Breadth-first distances from ``start`` to every reachable cell."""
    if not grid.contains(start):
        raise ValueError(f"{start} is outside the grid")
    distances = {start: 0}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for other in sorted(grid.passages(cell)):
            if other not in distances:
                distances[other] = distances[cell] + 1
                queue.append(other)
    return distances


def shortest_path(grid: Grid, start: Cell, goal: Cell) -> list[Cell]:
    """A* (Manhattan heuristic) shortest path, or ``[]`` if unreachable."""
    for cell in (start, goal):
        if not grid.contains(cell):
            raise ValueError(f"{cell} is outside the grid")
    if start == goal:
        return [start]

    def heuristic(cell: Cell) -> int:
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    came_from: dict[Cell, Cell] = {}
    best = {start: 0}
    queue: list[tuple[int, int, Cell]] = [(heuristic(start), 0, start)]
    while queue:
        _, cost, cell = heapq.heappop(queue)
        if cell == goal:
            path = [cell]
            while cell in came_from:
                cell = came_from[cell]
                path.append(cell)
            return path[::-1]
        if cost > best.get(cell, cost):
            continue
        for other in sorted(grid.passages(cell)):
            step = cost + 1
            if step < best.get(other, step + 1):
                best[other] = step
                came_from[other] = cell
                heapq.heappush(queue, (step + heuristic(other), step, other))
    return []


def longest_path(grid: Grid) -> list[Cell]:
    """The maze's "diameter": the longest shortest-path in a perfect maze."""
    origin = next(grid.cells())
    far = max(flood(grid, origin).items(), key=lambda item: (item[1], item[0]))[0]
    other = max(flood(grid, far).items(), key=lambda item: (item[1], item[0]))[0]
    return shortest_path(grid, far, other)


def dead_ends(grid: Grid) -> list[Cell]:
    return [cell for cell in grid.cells() if len(grid.passages(cell)) == 1]


def is_perfect(grid: Grid) -> bool:
    """True when the maze is fully connected and loop-free (a spanning tree)."""
    edge_count = sum(1 for _ in grid.edges())
    return edge_count == len(grid) - 1 and len(flood(grid, next(grid.cells()))) == len(grid)


def stats(grid: Grid) -> dict[str, float | int]:
    """Summary metrics used by the CLI's ``--stats`` flag."""
    path = longest_path(grid)
    ends = dead_ends(grid)
    junctions = [cell for cell in grid.cells() if len(grid.passages(cell)) > 2]
    return {
        "cells": len(grid),
        "passages": sum(1 for _ in grid.edges()),
        "dead_ends": len(ends),
        "junctions": len(junctions),
        "diameter": len(path),
        "perfect": is_perfect(grid),
        "dead_end_ratio": round(len(ends) / len(grid), 3),
    }
