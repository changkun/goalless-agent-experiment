#!/usr/bin/env python3
"""Generate a random perfect maze and solve it, rendering both to the terminal.

Usage:
    python3 maze.py [WIDTH] [HEIGHT] [--seed N] [--no-solve]
"""

from __future__ import annotations

import argparse
import random
from collections import deque
from dataclasses import dataclass, field

DIRECTIONS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


@dataclass
class Maze:
    width: int
    height: int
    walls: dict[tuple[int, int], set[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("maze dimensions must be positive")
        if not self.walls:
            self.walls = {
                (x, y): set(DIRECTIONS)
                for y in range(self.height)
                for x in range(self.width)
            }

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def carve(self, x: int, y: int, direction: str) -> None:
        dx, dy = DIRECTIONS[direction]
        nx, ny = x + dx, y + dy
        if not self.in_bounds(nx, ny):
            raise ValueError("cannot carve outside the maze")
        self.walls[(x, y)].discard(direction)
        self.walls[(nx, ny)].discard(OPPOSITE[direction])

    def neighbors(self, x: int, y: int):
        for direction, (dx, dy) in DIRECTIONS.items():
            if direction not in self.walls[(x, y)]:
                yield x + dx, y + dy


def generate(width: int, height: int, rng: random.Random | None = None) -> Maze:
    """Carve a perfect maze (exactly one path between any two cells) via iterative DFS."""
    rng = rng or random.Random()
    maze = Maze(width, height)
    start = (rng.randrange(width), rng.randrange(height))
    visited = {start}
    stack = [start]
    while stack:
        x, y = stack[-1]
        options = [
            (direction, (x + dx, y + dy))
            for direction, (dx, dy) in DIRECTIONS.items()
            if maze.in_bounds(x + dx, y + dy) and (x + dx, y + dy) not in visited
        ]
        if not options:
            stack.pop()
            continue
        direction, cell = rng.choice(options)
        maze.carve(x, y, direction)
        visited.add(cell)
        stack.append(cell)
    return maze


def solve(maze: Maze, start=(0, 0), goal=None) -> list[tuple[int, int]]:
    """Shortest path from start to goal using breadth-first search."""
    goal = goal or (maze.width - 1, maze.height - 1)
    parents = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in maze.neighbors(*cell):
            if nxt not in parents:
                parents[nxt] = cell
                queue.append(nxt)
    if goal not in parents:
        return []
    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = parents[cell]
    path.reverse()
    return path


def render(maze: Maze, path: list[tuple[int, int]] | None = None) -> str:
    """Render as box characters; path cells are marked with '·', endpoints with S/G."""
    on_path = set(path or [])
    start = path[0] if path else None
    goal = path[-1] if path else None
    lines = ["+" + "---+" * maze.width]
    for y in range(maze.height):
        row = "|"
        floor = "+"
        for x in range(maze.width):
            cell = (x, y)
            if cell == start:
                mark = " S "
            elif cell == goal:
                mark = " G "
            elif cell in on_path:
                mark = " · "
            else:
                mark = "   "
            row += mark + ("|" if "E" in maze.walls[cell] else " ")
            floor += ("---" if "S" in maze.walls[cell] else "   ") + "+"
        lines.append(row)
        lines.append(floor)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("width", nargs="?", type=int, default=20)
    parser.add_argument("height", nargs="?", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-solve", action="store_true")
    args = parser.parse_args(argv)

    maze = generate(args.width, args.height, random.Random(args.seed))
    path = None if args.no_solve else solve(maze)
    print(render(maze, path))
    if path:
        print(f"\nSolved in {len(path) - 1} steps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
