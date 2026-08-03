"""A tiny, dependency-free maze generator and solver.

The maze is an ASCII grid rendered on a character lattice. Each cell is
represented by four walls (N, E, S, W). We generate a perfect maze with
recursive backtracking, then solve it with a depth-first search.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator

WALL = "#"
PATH = " "
START = "S"
END = "E"
VISITED = "."

# Direction helpers as (row, col) deltas keyed by wall names.
_DIRS = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}
_OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


@dataclass
class Cell:
    """A single maze cell holding its four walls."""

    row: int
    col: int
    walls: set[str]

    @property
    def neighbors(self) -> Iterator[str]:
        return iter(self.walls)


class Maze:
    def __init__(self, rows: int, cols: int, seed: int | None = None) -> None:
        if rows < 2 or cols < 2:
            raise ValueError("Maze must be at least 2x2 cells.")
        self.rows = rows
        self.cols = cols
        self._rng = random.Random(seed)
        self.start = (0, 0)
        self.end = (rows - 1, cols - 1)
        self.grid = {
            (r, c): Cell(r, c, set(_DIRS))
            for r in range(rows)
            for c in range(cols)
        }
        self._carve()

    # -- generation -----------------------------------------------------
    def _carve(self) -> None:
        """Recursive-backtracking pass that removes walls to make a maze."""
        visited: set[tuple[int, int]] = set()
        stack: list[tuple[int, int]] = [self.start]

        while stack:
            row, col = stack[-1]
            if (row, col) not in visited:
                visited.add((row, col))

            neighbors = [
                (d, r, c)
                for d, (dr, dc) in _DIRS.items()
                if (
                    0 <= (r := row + dr) < self.rows
                    and 0 <= (c := col + dc) < self.cols
                    and (r, c) not in visited
                )
            ]

            if not neighbors:
                stack.pop()
                continue

            direction, nrow, ncol = self._rng.choice(neighbors)
            self.grid[(row, col)].walls.discard(direction)
            self.grid[(nrow, ncol)].walls.discard(_OPPOSITE[direction])
            stack.append((nrow, ncol))

    # -- rendering ------------------------------------------------------
    def render(self) -> str:
        """Render the maze to a printable string.

        We start from a fully-walled character grid and punch openings based
        on each cell's carved walls. The outer border always stays intact.
        """
        height = self.rows * 2 + 1
        width = self.cols * 2 + 1
        out = [[WALL] * width for _ in range(height)]

        for (r, c), cell in self.grid.items():
            out[r * 2 + 1][c * 2 + 1] = PATH
            if "N" not in cell.walls:
                out[r * 2][c * 2 + 1] = PATH
            if "S" not in cell.walls:
                out[r * 2 + 2][c * 2 + 1] = PATH
            if "W" not in cell.walls:
                out[r * 2 + 1][c * 2] = PATH
            if "E" not in cell.walls:
                out[r * 2 + 1][c * 2 + 2] = PATH

        # Mark the entrance and exit cells.
        sr, sc = self.start
        out[sr * 2 + 1][sc * 2 + 1] = START
        er, ec = self.end
        out[er * 2 + 1][ec * 2 + 1] = END

        return "\n".join("".join(row) for row in out)

    def line(self, index: int) -> str:
        """Render a single row of the maze as a string."""
        return self.render().splitlines()[index]

    # -- solving --------------------------------------------------------
    def solve(self) -> list[tuple[int, int]]:
        """Return the path of (row, col) cells from start to end.

        Uses iterative DFS with an explicit stack. Raises if no path exists
        (which cannot happen for a perfect maze, since every cell is reachable).
        """
        start = self.start
        end = self.end
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        stack = [start]

        while stack:
            cell = stack.pop()
            if cell == end:
                path = []
                cur: tuple[int, int] | None = end
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                return path

            row, col = cell
            # `walls` holds the directions that are BLOCKED; a cell is
            # traversable in a direction only when that wall is absent.
            for direction in _DIRS:
                if direction in self.grid[cell].walls:
                    continue
                dr, dc = _DIRS[direction]
                nxt = (row + dr, col + dc)
                if not (0 <= nxt[0] < self.rows and 0 <= nxt[1] < self.cols):
                    continue
                if nxt not in parent:
                    parent[nxt] = cell
                    stack.append(nxt)

        raise RuntimeError("No path found between start and end.")
