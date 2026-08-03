"""Core Game of Life logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

Point = tuple[int, int]

# Classic patterns as (width, height, live cells).
PRESETS: dict[str, tuple[int, int, frozenset[Point]]] = {
    "blinker": (
        3,
        3,
        frozenset({(1, 0), (1, 1), (1, 2)}),
    ),
    "block": (
        2,
        2,
        frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    ),
    "glider": (
        3,
        3,
        frozenset({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}),
    ),
    "pulsar": (
        13,
        13,
        frozenset(
            {
                (2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12),
                (4, 2), (5, 2), (6, 2), (10, 2), (11, 2), (12, 2),
                (4, 7), (5, 7), (6, 7), (10, 7), (11, 7), (12, 7),
                (4, 9), (5, 9), (6, 9), (10, 9), (11, 9), (12, 9),
                (7, 4), (7, 5), (7, 6), (7, 10), (7, 11), (7, 12),
                (9, 4), (9, 5), (9, 6), (9, 10), (9, 11), (9, 12),
            }
        ),
    ),
}


def _neighbors(p: Point) -> Iterable[Point]:
    r, c = p
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            yield (r + dr, c + dc)


def next_generation(live: set[Point]) -> set[Point]:
    """Return the set of live cells in the next generation."""
    counts: dict[Point, int] = {}
    for cell in live:
        for n in _neighbors(cell):
            counts[n] = counts.get(n, 0) + 1
    return {
        cell
        for cell, count in counts.items()
        if count == 3 or (cell in live and count == 2)
    }


def parse_pattern(text: str) -> set[Point]:
    """Parse a plain-text grid of live (O/#) and dead (.) cells into points."""
    alive = {"O", "o", "#", "X", "x", "*"}
    cells: set[Point] = set()
    for r, line in enumerate(text.splitlines()):
        for c, ch in enumerate(line):
            if ch in alive:
                cells.add((r, c))
    return cells


def render(live: set[Point], live_char: str = "o") -> str:
    """Render live cells as a string clipped to their bounding box."""
    if not live:
        return ""
    rows = [r for r, _ in live]
    cols = [c for _, c in live]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)
    lines = []
    for r in range(min_r, max_r + 1):
        lines.append(
            "".join(live_char if (r, c) in live else "." for c in range(min_c, max_c + 1))
        )
    return "\n".join(lines)


@dataclass
class Game:
    """A bounded Game of Life board."""

    width: int
    height: int
    live: set[Point] = field(default_factory=set)
    generation: int = 0
    wrap: bool = False

    def __post_init__(self) -> None:
        self._trim()

    def _trim(self) -> None:
        self.live = {p for p in self.live if 0 <= p[0] < self.height and 0 <= p[1] < self.width}

    def load(self, pattern: str) -> "Game":
        """Load a pattern, centered on the board."""
        width, height, cells = PRESETS[pattern]
        dr = (self.height - height) // 2
        dc = (self.width - width) // 2
        self.live = {
            (r + dr, c + dc)
            for (r, c) in cells
            if 0 <= r + dr < self.height and 0 <= c + dc < self.width
        }
        self.generation = 0
        return self

    def step(self) -> None:
        next_live = next_generation(self.live)
        if self.wrap:
            next_live = {(r % self.height, c % self.width) for r, c in next_live}
        self.live = {p for p in next_live if 0 <= p[0] < self.height and 0 <= p[1] < self.width}
        self.generation += 1

    def board(self, live_char: str = "o") -> str:
        return "\n".join(
            "".join(live_char if (r, c) in self.live else "." for c in range(self.width))
            for r in range(self.height)
        )

    def population(self) -> int:
        return len(self.live)
