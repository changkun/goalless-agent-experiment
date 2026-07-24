"""Pathfinding algorithms that record their search order for replay."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

from pathviz.grid import Cell, Grid

ALGORITHMS = ("bfs", "dfs", "dijkstra", "astar")


@dataclass
class SearchResult:
    """Outcome of a search plus enough history to animate it."""

    algorithm: str
    path: list[Cell]
    visited: list[Cell] = field(default_factory=list)
    frontier_sizes: list[int] = field(default_factory=list)
    cost: int = 0

    @property
    def found(self) -> bool:
        return bool(self.path)

    @property
    def expanded(self) -> int:
        return len(self.visited)

    @property
    def peak_frontier(self) -> int:
        return max(self.frontier_sizes, default=0)


def search(grid: Grid, algorithm: str = "bfs") -> SearchResult:
    """Run ``algorithm`` from ``grid.start`` to ``grid.goal``."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f"unknown algorithm {algorithm!r}; expected one of {ALGORITHMS}")
    if not grid.is_floor(grid.start) or not grid.is_floor(grid.goal):
        raise ValueError("start and goal must both be floor cells")

    if algorithm in ("bfs", "dfs"):
        visited, frontier_sizes, parents = _uninformed(grid, depth_first=algorithm == "dfs")
    else:
        visited, frontier_sizes, parents = _best_first(grid, heuristic=algorithm == "astar")

    path = _reconstruct(parents, grid.start, grid.goal)
    return SearchResult(
        algorithm=algorithm,
        path=path,
        visited=visited,
        frontier_sizes=frontier_sizes,
        cost=grid.path_cost(path),
    )


def _uninformed(
    grid: Grid, depth_first: bool
) -> tuple[list[Cell], list[int], dict[Cell, Cell | None]]:
    """BFS (queue) or DFS (stack); both ignore terrain cost."""
    frontier: deque[Cell] = deque([grid.start])
    parents: dict[Cell, Cell | None] = {grid.start: None}
    visited: list[Cell] = []
    frontier_sizes: list[int] = []

    while frontier:
        cell = frontier.pop() if depth_first else frontier.popleft()
        visited.append(cell)
        frontier_sizes.append(len(frontier))
        if cell == grid.goal:
            break
        for neighbor in grid.neighbors(cell):
            if neighbor not in parents:
                parents[neighbor] = cell
                frontier.append(neighbor)
    return visited, frontier_sizes, parents


def _best_first(
    grid: Grid, heuristic: bool
) -> tuple[list[Cell], list[int], dict[Cell, Cell | None]]:
    """Dijkstra, or A* with a Manhattan heuristic when ``heuristic`` is set."""
    start, goal = grid.start, grid.goal
    best_cost: dict[Cell, int] = {start: 0}
    parents: dict[Cell, Cell | None] = {start: None}
    visited: list[Cell] = []
    frontier_sizes: list[int] = []
    settled: set[Cell] = set()
    heap: list[tuple[int, int, Cell]] = [(_h(start, goal) if heuristic else 0, 0, start)]

    while heap:
        _, cost, cell = heapq.heappop(heap)
        if cell in settled:
            continue
        settled.add(cell)
        visited.append(cell)
        frontier_sizes.append(len(heap))
        if cell == goal:
            break
        for neighbor in grid.neighbors(cell):
            new_cost = cost + grid.weight(neighbor)
            if new_cost < best_cost.get(neighbor, 1 << 60):
                best_cost[neighbor] = new_cost
                parents[neighbor] = cell
                priority = new_cost + (_h(neighbor, goal) if heuristic else 0)
                heapq.heappush(heap, (priority, new_cost, neighbor))
    return visited, frontier_sizes, parents


def _h(cell: Cell, goal: Cell) -> int:
    return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])


def _reconstruct(parents: dict[Cell, Cell | None], start: Cell, goal: Cell) -> list[Cell]:
    if goal not in parents:
        return []
    path = [goal]
    while path[-1] != start:
        parent = parents[path[-1]]
        if parent is None:
            return []
        path.append(parent)
    path.reverse()
    return path
