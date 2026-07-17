"""Simulation grid for Conway's Game of Life and variants.

A Grid is a torus: edges wrap, so patterns drift forever without
hitting walls. State is a flat bytearray of 0/1 for speed.
"""

from __future__ import annotations


class Grid:
    __slots__ = ("w", "h", "cells")

    def __init__(self, w, h, cells=None):
        if w <= 0 or h <= 0:
            raise ValueError("grid dimensions must be positive")
        self.w = w
        self.h = h
        self.cells = cells if cells is not None else bytearray(w * h)

    def index(self, x, y):
        return (y % self.h) * self.w + (x % self.w)

    def get(self, x, y):
        return self.cells[self.index(x, y)]

    def set(self, x, y, v):
        self.cells[self.index(x, y)] = 1 if v else 0

    def population(self):
        return sum(self.cells)

    def neighbor_count(self, x, y):
        w, h, c = self.w, self.h, self.cells
        left = (x - 1) % w
        right = (x + 1) % w
        up = (y - 1) % h
        down = (y + 1) % h
        return (
            c[up * w + left] + c[up * w + x] + c[up * w + right]
            + c[y * w + left] + c[y * w + right]
            + c[down * w + left] + c[down * w + x] + c[down * w + right]
        )

    def signature(self):
        """Position-exact identity of the current state.

        Exact cycle detection: a repeated signature means the automaton
        has provably entered a loop (on a torus, spaceships never repeat
        a position unless the wrap coincides with their period).
        """
        return bytes(self.cells)

    def ascii(self):
        lines = []
        for y in range(self.h):
            row = self.cells[y * self.w:(y + 1) * self.w]
            lines.append("".join("#" if v else "." for v in row))
        return "\n".join(lines)
