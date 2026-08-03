"""A small collection of classic Game of Life patterns.

Each pattern is stored as rows of ``.`` (dead) and ``#`` (live) characters.
Patterns that oscillate are given a couple of cells of dead margin around
them, because the simulation runs on a bounded grid and intermediate phases
may extend beyond the stripes visible at generation 0.
"""

from __future__ import annotations

from life import Grid


PATTERNS: dict[str, Grid] = {
    # Moveable spaceship that travels diagonally, one cell every 4
    # generations. The simplest and best-known moving pattern.
    "glider": Grid.from_rows([
        ".#.",
        "..#",
        "###",
    ]),
    # Simplest oscillator: a horizontal line of three that flips vertical
    # and back, with period 2. The dead margin lets it rotate without
    # clipping the grid edge.
    "blinker": Grid.from_rows([
        ".......",
        ".......",
        "..###..",
        ".......",
        ".......",
    ]),
    # Period-2 oscillator shaped like (unsurprisingly) a toad.
    "toad": Grid.from_rows([
        "........",
        "........",
        "...###..",
        "..###...",
        "........",
        "........",
    ]),
    # Period-2 oscillator of four adjacent blocks that blink as a pair.
    "beacon": Grid.from_rows([
        "##..",
        "##..",
        "..##",
        "..##",
    ]),
    # A well-known period-3 oscillator: four L-shaped groups of cells that
    # rotate through three phases before returning to the start.
    "pulsar": Grid.from_rows([
        ".................",
        ".................",
        "....###...###....",
        ".................",
        "..#....#.#....#..",
        "..#....#.#....#..",
        "..#....#.#....#..",
        "....###...###....",
        ".................",
        "....###...###....",
        "..#....#.#....#..",
        "..#....#.#....#..",
        "..#....#.#....#..",
        ".................",
        "....###...###....",
        ".................",
        ".................",
    ]),
    # The smallest known infinite-growth pattern: the Gosper glider gun.
    # Firings of a glider every 30 generations let the population grow
    # without bound, so it needs a roomy margin to see the growth.
    "gun": Grid.from_rows([
        ".........................O...........",
        ".......................O.O...........",
        "..............OO......OO............OO",
        ".............O...O....OO............OO",
        "OO..........O.....O...OO..............",
        "OO..........O...O.OO....O.O...........",
        "...........O.....O.......O...........",
        "............O...O....................",
        "..............OO.....................",
    ]),
}
