#!/usr/bin/env python3
"""Generate a maze with recursive backtracking, then solve it with A*.

Renders the maze and the discovered path to the terminal with ANSI color.
Pure standard library, no dependencies.

    python3 maze.py            # default 25x15
    python3 maze.py 41 21      # custom width height (odd numbers look best)
    python3 maze.py 41 21 7    # ...with a fixed RNG seed for reproducibility
"""
from __future__ import annotations

import heapq
import random
import sys
from typing import Iterator

# A cell-grid maze. We work in "cell" coordinates and expand to a character
# grid for rendering, where walls live between cells.
WALL, OPEN = 0, 1


class Maze:
    def __init__(self, cols: int, rows: int, seed: int | None = None):
        self.cols = cols
        self.rows = rows
        self.rng = random.Random(seed)
        # Walls between neighbouring cells: a set of frozenset({a, b}) pairs
        # that have been carved open.
        self.links: set[frozenset[tuple[int, int]]] = set()
        self._carve()

    def _neighbours(self, c: int, r: int) -> Iterator[tuple[int, int]]:
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < self.cols and 0 <= nr < self.rows:
                yield nc, nr

    def _carve(self) -> None:
        """Recursive backtracker (iterative, to avoid recursion limits)."""
        start = (0, 0)
        visited = {start}
        stack = [start]
        while stack:
            c, r = stack[-1]
            unvisited = [n for n in self._neighbours(c, r) if n not in visited]
            if not unvisited:
                stack.pop()
                continue
            nxt = self.rng.choice(unvisited)
            self.links.add(frozenset({(c, r), nxt}))
            visited.add(nxt)
            stack.append(nxt)

    def linked(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        return frozenset({a, b}) in self.links

    def solve(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        """A* over the carved passages. Manhattan distance heuristic."""
        def h(p: tuple[int, int]) -> int:
            return abs(p[0] - goal[0]) + abs(p[1] - goal[1])

        open_heap: list[tuple[int, int, tuple[int, int]]] = [(h(start), 0, start)]
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score = {start: 0}
        while open_heap:
            _, g, cur = heapq.heappop(open_heap)
            if cur == goal:
                path = [cur]
                while cur in came_from:
                    cur = came_from[cur]
                    path.append(cur)
                return path[::-1]
            for nb in self._neighbours(*cur):
                if not self.linked(cur, nb):
                    continue
                tentative = g + 1
                if tentative < g_score.get(nb, 1 << 30):
                    came_from[nb] = cur
                    g_score[nb] = tentative
                    heapq.heappush(open_heap, (tentative + h(nb), tentative, nb))
        return []


# ---- Rendering -------------------------------------------------------------

RESET = "\033[0m"
DIM = "\033[38;5;240m"      # walls
PATH = "\033[1;38;5;82m"    # solution path (bright green)
ENDS = "\033[1;38;5;208m"   # start / goal markers (orange)


def render(maze: Maze, path: list[tuple[int, int]], color: bool) -> str:
    on_path = set(path)
    start, goal = path[0], path[-1]
    w, h = maze.cols, maze.rows

    def wall(s: str) -> str:
        return f"{DIM}{s}{RESET}" if color else s

    out: list[str] = []
    # Top border.
    out.append(wall("+" + "---+" * w))
    for r in range(h):
        # Cell row: each cell is 3 chars wide, walls between are "|".
        top = wall("|")
        for c in range(w):
            cell = (c, r)
            if cell == start:
                body = f"{ENDS} S {RESET}" if color else " S "
            elif cell == goal:
                body = f"{ENDS} G {RESET}" if color else " G "
            elif cell in on_path:
                body = f"{PATH} * {RESET}" if color else " * "
            else:
                body = "   "
            # East wall.
            if c + 1 < w and maze.linked(cell, (c + 1, r)):
                # Passage open: keep path colour continuous if both on path.
                if color and cell in on_path and (c + 1, r) in on_path:
                    east = f"{PATH}*{RESET}"
                else:
                    east = " "
            else:
                east = wall("|")
            top += body + east
        out.append(top)
        # Wall row below this cell row.
        bottom = wall("+")
        for c in range(w):
            cell = (c, r)
            if r + 1 < h and maze.linked(cell, (c, r + 1)):
                if color and cell in on_path and (c, r + 1) in on_path:
                    seg = f"{PATH} * {RESET}"
                else:
                    seg = "   "
            else:
                seg = wall("---")
            bottom += seg + wall("+")
        out.append(bottom)
    return "\n".join(out)


def main(argv: list[str]) -> int:
    cols = int(argv[1]) if len(argv) > 1 else 25
    rows = int(argv[2]) if len(argv) > 2 else 15
    seed = int(argv[3]) if len(argv) > 3 else None
    color = sys.stdout.isatty()

    maze = Maze(cols, rows, seed)
    path = maze.solve((0, 0), (cols - 1, rows - 1))

    print(render(maze, path, color))
    print(f"\n{cols}x{rows} maze  ·  shortest path: {len(path)} cells"
          + (f"  ·  seed {seed}" if seed is not None else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
