#!/usr/bin/env python3
"""Conway's Game of Life — terminal edition.

Self-contained: no external deps beyond the Python standard library.
Includes classic patterns (glider, pulsar, blinker, gosper gun).
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
import time
from dataclasses import dataclass


DEAD, ALIVE = 0, 1

# ANSI 256-color palette picks for variety by cell age.
COLORS = [
    "\033[38;5;39m",   # cyan
    "\033[38;5;48m",   # green
    "\033[38;5;190m",  # yellow-green
    "\033[38;5;214m",  # orange
    "\033[38;5;203m",  # pink
    "\033[38;5;129m",  # purple
]
RESET = "\033[0m"


# ---- Patterns (relative coords as list of (row, col)) ----------------------
def _pattern(rows: list[str]) -> list[tuple[int, int]]:
    out = []
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch != " " and ch != ".":
                out.append((r, c))
    return out


PATTERNS: dict[str, list[tuple[int, int]]] = {
    "glider": _pattern([
        ".O.",
        "..O",
        "OOO",
    ]),
    "blinker": _pattern(["OOO"]),
    "toad": _pattern([
        ".OOO",
        "OOO.",
    ]),
    "beacon": _pattern([
        "OO..",
        "OO..",
        "..OO",
        "..OO",
    ]),
    "pulsar": _pattern([
        "..OOO...OOO..",
        ".............",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        ".............",
        "..OOO...OOO..",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        ".............",
        "..OOO...OOO..",
    ]),
    "gosper": _pattern([
        "........................O...........",
        "......................O.O...........",
        "............OO......OO............OO",
        "...........O...O....OO............OO",
        "OO........O.....O...OO..............",
        "OO........O...O.OO....O.O...........",
        "..........O.....O.......O...........",
        "...........O...O....................",
        "............OO......................",
    ]),
}


@dataclass(slots=True)
class Grid:
    w: int
    h: int
    cells: list[int]   # current state
    ages: list[int]    # how long a cell has been alive (for color)

    @classmethod
    def blank(cls, w: int, h: int) -> "Grid":
        n = w * h
        return cls(w=w, h=h, cells=[DEAD] * n, ages=[0] * n)

    def idx(self, x: int, y: int) -> int:
        return y * self.w + x

    def set(self, x: int, y: int, v: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self.idx(x, y)
            self.cells[i] = v
            if v == ALIVE:
                self.ages[i] = 1

    def stamp(self, pattern: list[tuple[int, int]], ox: int, oy: int) -> None:
        for r, c in pattern:
            self.set(ox + c, oy + r, ALIVE)

    def step(self) -> None:
        w, h = self.w, self.h
        cells = self.cells
        ages = self.ages
        new_cells = list(cells)
        new_ages = list(ages)
        for y in range(h):
            for x in range(w):
                i = y * w + x
                n = 0
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        continue
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = x + dx
                        if nx < 0 or nx >= w:
                            continue
                        n += cells[ny * w + nx]
                alive = cells[i] == ALIVE
                if alive and (n == 2 or n == 3):
                    new_cells[i] = ALIVE
                    new_ages[i] = ages[i] + 1
                elif not alive and n == 3:
                    new_cells[i] = ALIVE
                    new_ages[i] = 1
                else:
                    new_cells[i] = DEAD
                    new_ages[i] = 0
        self.cells = new_cells
        self.ages = new_ages

    def render(self, alive_char: str = "o") -> str:
        out: list[str] = []
        out.append("\033[H")  # move cursor home
        for y in range(self.h):
            row: list[str] = []
            for x in range(self.w):
                i = self.idx(x, y)
                if self.cells[i] == ALIVE:
                    age = self.ages[i]
                    color = COLORS[min(age - 1, len(COLORS) - 1)]
                    row.append(f"{color}{alive_char}{RESET}")
                else:
                    row.append(" ")
            out.append("".join(row))
        # status line
        live = sum(1 for c in self.cells if c == ALIVE)
        out.append(f"\033[38;5;245mgen={self._gen}  alive={live}  (Ctrl-C to quit)\033[0m")
        return "\n".join(out)

    _gen: int = 0

    def advance(self) -> None:
        self.step()
        self._gen += 1


def term_size() -> tuple[int, int]:
    cols, lines = shutil.get_terminal_size((80, 24))
    return cols, lines - 1  # leave a line for status


def build_grid(args) -> Grid:
    w, h = term_size()
    grid = Grid.blank(w, h)
    if args.random:
        density = args.density
        rng = random.Random(args.seed)
        for i in range(w * h):
            if rng.random() < density:
                grid.cells[i] = ALIVE
                grid.ages[i] = 1
        return grid
    if args.pattern:
        name = args.pattern.lower()
        if name not in PATTERNS:
            print(f"unknown pattern: {name}", file=sys.stderr)
            print(f"available: {', '.join(PATTERNS)}", file=sys.stderr)
            sys.exit(2)
        grid.stamp(PATTERNS[name], w // 2 - 5, h // 2 - 4)
        return grid
    # default: a nice mix
    grid.stamp(PATTERNS["glider"], 3, 3)
    grid.stamp(PATTERNS["pulsar"], w // 2 - 6, h // 2 - 6)
    grid.stamp(PATTERNS["gosper"], w - 38, h - 10)
    return grid


def main() -> None:
    ap = argparse.ArgumentParser(description="Conway's Game of Life in your terminal.")
    ap.add_argument("-r", "--random", action="store_true", help="random soup start")
    ap.add_argument("-d", "--density", type=float, default=0.3,
                    help="density for random mode (0..1)")
    ap.add_argument("-p", "--pattern", help=f"named pattern: {', '.join(PATTERNS)}")
    ap.add_argument("-i", "--interval", type=float, default=0.08,
                    help="seconds between generations")
    ap.add_argument("-s", "--seed", type=int, default=None, help="RNG seed")
    ap.add_argument("-n", "--generations", type=int, default=0,
                    help="stop after N generations (0 = forever)")
    args = ap.parse_args()

    grid = build_grid(args)

    sys.stdout.write("\033[2J")  # clear screen
    try:
        while True:
            sys.stdout.write(grid.render() + "\n")
            sys.stdout.flush()
            if args.generations and grid._gen >= args.generations:
                break
            time.sleep(args.interval)
            grid.advance()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h")  # reset + show cursor
        print()


if __name__ == "__main__":
    main()
