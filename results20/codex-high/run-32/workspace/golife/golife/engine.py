"""Core Conway's Game of Life engine.

The universe is an infinite, edge-less plane represented as a set of
(x, y) coordinates for living cells. This keeps the simulation unbounded
while remaining efficient thanks to the neighbourhood-counting trick.
"""
from __future__ import annotations

from dataclasses import dataclass


class Universe:
    """An infinite grid of living cells."""

    def __init__(self, live: set[tuple[int, int]] | None = None) -> None:
        self._live: set[tuple[int, int]] = set(live or ())
        self.generation = 0

    @property
    def live(self) -> set[tuple[int, int]]:
        """The current set of living cells (a copy)."""
        return set(self._live)

    @property
    def population(self) -> int:
        return len(self._live)

    @property
    def alive(self) -> bool:
        return bool(self._live)

    def seed(self, cells: set[tuple[int, int]]) -> None:
        """Replace the current population with ``cells``."""
        self._live = set(cells)
        self.generation = 0

    def toggle(self, x: int, y: int) -> None:
        """Flip the state of the cell at (x, y)."""
        if (x, y) in self._live:
            self._live.remove((x, y))
        else:
            self._live.add((x, y))

    def step(self, generations: int = 1) -> "Universe":
        """Advance the simulation by ``generations`` ticks and return self."""
        for _ in range(generations):
            self._step_once()
        return self

    def _step_once(self) -> None:
        neighbours: dict[tuple[int, int], int] = {}
        for x, y in self._live:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    key = (x + dx, y + dy)
                    neighbours[key] = neighbours.get(key, 0) + 1

        next_live: set[tuple[int, int]] = set()
        for cell, count in neighbours.items():
            if count == 3 or (count == 2 and cell in self._live):
                next_live.add(cell)
        self._live = next_live
        self.generation += 1

    def tick(self) -> "Universe":
        """Alias for a single ``step``."""
        return self.step(1)

    def bounds(self) -> tuple[int, int, int, int] | None:
        """Return (min_x, min_y, max_x, max_y) or None when empty."""
        if not self._live:
            return None
        xs = [x for x, _ in self._live]
        ys = [y for _, y in self._live]
        return min(xs), min(ys), max(xs), max(ys)

    def render(self, width: int | None = None, height: int | None = None,
               live: str = "#", dead: str = " ") -> str:
        """Render the live cells to a string.

        Without explicit dimensions the output is cropped to the live
        bounding box. With dimensions the grid is centred inside the
        given area.
        """
        if not self._live:
            return ""
        min_x, min_y, max_x, max_y = self.bounds()
        if width is None:
            width = max_x - min_x + 1
            offset_x = min_x
        else:
            span = max_x - min_x + 1
            offset_x = min_x - ((width - span) // 2)
        if height is None:
            height = max_y - min_y + 1
            offset_y = min_y
        else:
            span_h = max_y - min_y + 1
            offset_y = min_y - ((height - span_h) // 2)

        rows: list[str] = []
        for gy in range(offset_y, offset_y + height):
            row = "".join(
                live if (gx, gy) in self._live else dead
                for gx in range(offset_x, offset_x + width)
            )
            rows.append(row)
        return "\n".join(rows)

    def __repr__(self) -> str:
        return f"Universe(generation={self.generation}, population={self.population})"


@dataclass(frozen=True)
class Pattern:
    """A named, reusable dot-matrix pattern loaded from a string."""
    name: str
    rows: tuple[str, ...]

    def cells(self, x: int = 0, y: int = 0) -> set[tuple[int, int]]:
        """Convert the pattern to absolute coordinates with origin (x, y)."""
        result: set[tuple[int, int]] = set()
        for row_offset, row in enumerate(self.rows):
            for col_offset, char in enumerate(row):
                if char in ("*", "O", "#", "o"):
                    result.add((x + col_offset, y + row_offset))
        return result
