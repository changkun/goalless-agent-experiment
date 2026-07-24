#!/usr/bin/env python3
"""Invariant checks for the WFC solver.

The interesting properties are structural, not visual: every pipe end must
meet a matching pipe end, nothing may dangle off the canvas, and thin must
never splice into thick. Those all reduce to "facing sockets are equal", so
one check covers them if we run it over enough seeds and grid shapes.
"""

import random
import sys

from wfc import DELTA, OPPOSITE, TILES, Wave, popcount

GLYPH_TO_TILE = {t.glyph: t for t in TILES}


def check(rows: list[str]) -> None:
    h, w = len(rows), len(rows[0])
    for y in range(h):
        assert len(rows[y]) == w, "ragged output"
        for x in range(w):
            tile = GLYPH_TO_TILE[rows[y][x]]
            for d in range(4):
                dx, dy = DELTA[d]
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    other = GLYPH_TO_TILE[rows[ny][nx]]
                    assert tile.sockets[d] == other.sockets[OPPOSITE[d]], (
                        f"socket mismatch at ({x},{y})->({nx},{ny}): "
                        f"{rows[y][x]!r} vs {rows[ny][nx]!r}"
                    )
                else:
                    assert tile.sockets[d] == 0, (
                        f"pipe dangles off the border at ({x},{y}): {rows[y][x]!r}"
                    )


def main() -> int:
    shapes = [(1, 1), (1, 9), (9, 1), (2, 2), (3, 17), (24, 8), (40, 12)]
    total_backtracks = 0
    runs = 0
    for w, h in shapes:
        for seed in range(12):
            wave = Wave(w, h, random.Random(seed))
            total_backtracks += wave.solve()
            rows = wave.rows()
            assert all(popcount(m) == 1 for m in wave.cells), "cell left undecided"
            check(rows)
            runs += 1

    # A 1x1 grid is sealed on all four sides, so blank is the only legal tile.
    assert Wave(1, 1, random.Random(0)).rows() == [" "], "1x1 must collapse to blank"

    # Same seed, same grid => same output. Nothing may leak in from global rng.
    a = Wave(30, 10, random.Random(99))
    a.solve()
    b = Wave(30, 10, random.Random(99))
    b.solve()
    assert a.rows() == b.rows(), "solver is not deterministic under a fixed seed"

    # Different seeds should not agree, or the tie-breaking noise is dead.
    c = Wave(30, 10, random.Random(100))
    c.solve()
    assert a.rows() != c.rows(), "different seeds produced identical grids"

    print(f"ok: {runs} grids valid, {total_backtracks} backtrack(s) total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
