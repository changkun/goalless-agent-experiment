"""RLE (run-length encoded) pattern loader and mechanical verification.

Conway's Life patterns are often distributed in RLE format (used by Golly,
LifeWiki, Catagolue, etc.). ``load_rle`` decodes that format into a
:class:`life.Grid`.

Also provides :func:`period` and :func:`is_gun`, small mechanical checks we
use to confirm a hand-drawn pattern is what it claims to be:
  * a period-3 oscillator must return to its exact starting state after 3
    generations, and
  * a glider gun must show unbounded (strictly increasing over a long run)
    population growth.
"""

from __future__ import annotations

import re

from life import Grid

# Strip comments and whitespace; keep the `x = .., y = ..` header and body.
_RLE_HEADER = re.compile(r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)\s*", re.I)


def load_rle(rle: str) -> Grid:
    """Parse an RLE pattern string into a :class:`Grid`.

    Dead cells are represented by ``b``, live cells by ``o``, and each row
    ends with ``$`` (a final ``!`` terminates the pattern). Optional counts
    prefix each run, e.g. ``2b3o`` = two dead then three live cells.
    """
    lines = []
    for line in rle.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    # The first line is the header; the rest is the encoded body.
    header = lines[0]
    match = _RLE_HEADER.search(header)
    if not match:
        raise ValueError("no `x = ..., y = ...` header found in RLE")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid RLE dimensions {width}x{height}")

    body = "".join(lines[1:]).split("!", 1)[0]

    grid = Grid(height, width)
    row = col = 0
    num = 0
    for ch in body:
        if ch.isdigit():
            num = num * 10 + int(ch)
            continue
        count = num if num else 1
        num = 0
        if ch == "b":
            col += count
        elif ch == "o":
            for _ in range(count):
                grid.set(row, col, True)
                col += 1
        elif ch == "$":
            row += count
            col = 0
        elif ch in "\r\n":
            continue
        else:
            raise ValueError(f"unexpected RLE character {ch!r}")
    return grid


def period(grid: Grid, limit: int = 500) -> int | None:
    """Return the oscillator period of ``grid``, or ``None`` if it never
    repeats within ``limit`` generations."""
    start = grid.render()
    probe = Grid(grid.rows, grid.cols)
    for r in range(grid.rows):
        for c in range(grid.cols):
            probe.set(r, c, grid.get(r, c))
    for step in range(1, limit + 1):
        probe.step()
        if probe.render() == start:
            return step
    return None


def is_gun(grid: Grid, generations: int = 120) -> bool:
    """Return whether ``grid`` shows continuous growth (a glider gun) by
    checking the live-cell count rises far above its starting value."""
    start = grid.alive_count()
    counts = [start]
    probe = Grid(grid.rows, grid.cols)
    for r in range(grid.rows):
        for c in range(grid.cols):
            probe.set(r, c, grid.get(r, c))
    for _ in range(generations):
        probe.step()
        counts.append(probe.alive_count())
    # A genuine gun keeps emitting gliders; population rises steadily.
    return counts[-1] > start + 10
