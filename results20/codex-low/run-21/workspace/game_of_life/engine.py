"""Core Conway's Game of Life engine.

Cells live on an infinite grid backed by a set of live coordinates.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Iterator


Point = tuple[int, int]

_NEIGHBOR_DELTAS: tuple[Point, ...] = (
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
)


@dataclass
class Board:
    """A set of live cells on an infinite grid."""

    live: set[Point] = field(default_factory=set)

    def add(self, x: int, y: int) -> None:
        """Bring a cell to life."""
        self.live.add((x, y))

    def remove(self, x: int, y: int) -> None:
        """Kill a live cell."""
        self.live.discard((x, y))

    def toggle(self, x: int, y: int) -> None:
        """Flip the state of a cell."""
        point = (x, y)
        if point in self.live:
            self.live.discard(point)
        else:
            self.live.add(point)

    def is_alive(self, x: int, y: int) -> bool:
        return (x, y) in self.live

    def population(self) -> int:
        return len(self.live)

    def step(self) -> None:
        """Advance the board by one generation."""
        neighbor_counts: dict[Point, int] = defaultdict(int)
        for x, y in self.live:
            for dx, dy in _NEIGHBOR_DELTAS:
                neighbor_counts[(x + dx, y + dy)] += 1

        next_live: set[Point] = set()
        for point, count in neighbor_counts.items():
            if count == 3 or (count == 2 and point in self.live):
                next_live.add(point)
        self.live = next_live

    def bounds(self) -> tuple[int, int, int, int] | None:
        """Bounding box of live cells as (min_x, min_y, max_x, max_y).

        Returns ``None`` for an empty board.
        """
        if not self.live:
            return None
        xs = [x for x, _ in self.live]
        ys = [y for _, y in self.live]
        return min(xs), min(ys), max(xs), max(ys)


def load_pattern(pattern: Iterable[Point]) -> Board:
    """Load a board from a list of live cell coordinates."""
    return Board(set(pattern))


def parse_rle(text: str) -> Board:
    """Parse a small subset of the Run Length Encoded (RLE) format.

    Supports the ``x``/``y`` header and a single trailing pattern body.
    Tags and comments are skipped.
    """
    live: set[Point] = set()
    x = y = 0
    run: int = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("x"):
            continue
        for char in line:
            if char.isdigit():
                run = run * 10 + int(char)
            elif char == "b":
                x += run or 1
                run = 0
            elif char == "o":
                for _ in range(run or 1):
                    live.add((x, y))
                    x += 1
                run = 0
            elif char == "$":
                y += run or 1
                x = 0
                run = 0
            elif char == "!":
                break
    return Board(live)
