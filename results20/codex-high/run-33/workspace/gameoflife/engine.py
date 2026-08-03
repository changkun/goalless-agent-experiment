"""Conway's Game of Life engine.

The world is an infinite grid of boolean cells, implemented as a sparse set of
live cell coordinates.  Only living cells and their neighbours are ever
inspected each generation, so the simulation is unbounded in size.
"""

from __future__ import annotations

from typing import Iterable, Iterator, Set, Tuple

Cell = Tuple[int, int]


# Eight neighbour offsets.
_NEIGHBOURS: Tuple[Cell, ...] = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
)


class World:
    """A sparse, unbounded Game of Life world."""

    def __init__(self, seed: Iterable[Cell] = ()) -> None:
        self._live: Set[Cell] = set(map(tuple, seed))

    def __contains__(self, cell: Cell) -> bool:
        return cell in self._live

    def __iter__(self) -> Iterator[Cell]:
        return iter(self._live)

    def __len__(self) -> int:
        return len(self._live)

    @property
    def alive(self) -> int:
        return len(self._live)

    @property
    def live(self) -> Set[Cell]:
        return self._live

    def set(self, cell: Cell, alive: bool = True) -> None:
        """Turn a cell on (or off if ``alive`` is False)."""
        cell = tuple(cell)
        if alive:
            self._live.add(cell)
        else:
            self._live.discard(cell)

    def toggle(self, cell: Cell) -> None:
        cell = tuple(cell)
        if cell in self._live:
            self._live.discard(cell)
        else:
            self._live.add(cell)

    def clear(self) -> None:
        self._live.clear()

    @staticmethod
    def _neighbours_of(cell: Cell) -> Iterator[Cell]:
        x, y = cell
        for dx, dy in _NEIGHBOURS:
            yield (x + dx, y + dy)

    def step(self) -> "World":
        """Advance one generation, returning a *new* World."""
        counts: dict[Cell, int] = {}
        for cell in self._live:
            for n in self._neighbours_of(cell):
                counts[n] = counts.get(n, 0) + 1

        next_live: Set[Cell] = set()
        # Cells with neighbours are candidates for survival or birth.
        for cell, count in counts.items():
            if count == 3 or (count == 2 and cell in self._live):
                next_live.add(cell)
        return World(next_live)

    def step_in_place(self) -> None:
        """Advance one generation in place, reusing this World."""
        next_world = self.step()
        self._live = next_world._live
