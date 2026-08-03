#!/usr/bin/env python3
"""Conway's Game of Life — an interactive terminal implementation.

Controls
--------
space    pause / resume
r        randomize the board
c        clear the board
+ / -    speed up / slow down
q        quit
"""
import argparse
import curses
import random
from time import sleep
from typing import Set, Tuple

Cell = Tuple[int, int]

NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1),
             (0, -1),          (0, 1),
             (1, -1),  (1, 0), (1, 1)]


def step(live: Set[Cell]) -> Set[Cell]:
    """Advance the simulation by one generation."""
    counts: dict[Cell, int] = {}
    for cell in live:
        for dr, dc in NEIGHBORS:
            n = (cell[0] + dr, cell[1] + dc)
            counts[n] = counts.get(n, 0) + 1
    return {
        cell for cell, n in counts.items()
        if n == 3 or (n == 2 and cell in live)
    }


def random_live(height: int, width: int, density: float = 0.28) -> Set[Cell]:
    return {
        (r, c) for r in range(height) for c in range(width)
        if random.random() < density
    }


def draw(stdscr, live: Set[Cell], paused: bool, gen: int,
         speed: float, height: int, width: int) -> None:
    stdscr.erase()
    for r, c in live:
        if 0 <= r < height and 0 <= c < width:
            try:
                stdscr.addch(r, c, "#")
            except curses.error:
                pass
    status = (
        f"gen {gen}  cells {len(live)}  "
        f"{'PAUSED' if paused else 'running'}  "
        f"{speed:.1f} gen/s   "
        "space pause  r random  c clear  +/- speed  q quit"
    )
    try:
        stdscr.addstr(height, 0, status[:width], curses.A_REVERSE)
    except curses.error:
        pass
    stdscr.refresh()


def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    height, width = stdscr.getmaxyx()
    height -= 1  # reserve the bottom line for the status bar

    live = random_live(height, width)
    gen = 0
    paused = False
    speed = 10.0

    while True:
        draw(stdscr, live, paused, gen, speed, height, width)

        if not paused:
            gen += 1
            live = step(live)

        sleep(1.0 / max(speed, 0.1))

        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == ord(" "):
            paused = not paused
        elif key == ord("r"):
            live = random_live(height, width)
            gen = 0
        elif key == ord("c"):
            live = set()
            gen = 0
        elif key in (ord("+"), ord("=")):
            speed = min(speed * 1.5, 60.0)
        elif key in (ord("-"), ord("_")):
            speed = max(speed / 1.5, 1.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive Conway's Game of Life in the terminal.")
    parser.add_argument("--seed", type=int, help="PRNG seed for reproducibility")
    return parser.parse_args()


def wrapper(stdscr) -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    main(stdscr)


if __name__ == "__main__":
    curses.wrapper(wrapper)
