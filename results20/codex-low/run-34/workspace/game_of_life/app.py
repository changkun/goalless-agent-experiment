"""Curses UI: run the simulation, draw, and edit cells by hand."""

from __future__ import annotations

import argparse
import curses
import random
import time

from .engine import Life
from .patterns import BLINKER, BLOCK, GLIDER

_PATTERNS = {"blinker": BLINKER, "block": BLOCK, "glider": GLIDER}

_BOARD_OFFSET = 2  # rows of status/help text above the board
_KEYS = {
    "step": 32,      # space
    "clear": ord("c"),
    "random": ord("r"),
    "quit": ord("q"),
    "pause": ord("p"),
    "slow": ord("-"),
    "fast": ord("+"),
}


def _draw(w: "curses.window", life: Life, population: int, paused: bool, speed: float) -> None:
    w.erase()
    w.addnstr(0, 0, f"Game of Life  |  population: {population}  |  {'paused' if paused else f'{speed:g} gen/s'}  |  "
                     f"space: step  r: random  c: clear  p: pause  +/-: speed  q: quit", 0)
    w.addnstr(1, 0, "mouse: toggle cell", 0)
    for row in range(life.height):
        for col in range(life.width):
            if life.is_alive(row, col):
                try:
                    w.addch(_BOARD_OFFSET + row, col, "█")
                except curses.error:
                    pass
    w.refresh()


def _run(stdscr: "curses.window", args: argparse.Namespace) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    try:
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED)
    except curses.error:
        pass

    height = max(10, min(40, curses.LINES - _BOARD_OFFSET))
    width = max(10, min(80, curses.COLS))
    life = Life(width, height, _PATTERNS[args.pattern])
    paused = True
    speed = 4.0
    next_frame = time.monotonic()

    while True:
        population = life.population()
        _draw(stdscr, life, population, paused, speed)

        if not paused:
            now = time.monotonic()
            while now >= next_frame:
                life.step()
                next_frame += 1.0 / speed
            delay = next_frame - now
        else:
            delay = 0.5

        ch = stdscr.getch()
        if ch == -1:
            if not paused:
                time.sleep(max(delay, 0.0))
            continue

        if ch == ord("q"):
            break
        if ch == ord(" "):
            life.step()
        elif ch == ord("p"):
            paused = not paused
            next_frame = time.monotonic()
        elif ch == ord("r"):
            height = max(10, min(40, curses.LINES - _BOARD_OFFSET))
            width = max(10, min(80, curses.COLS))
            life = Life(width, height)
            for _ in range(width * height // 5):
                life.live_cells.add((random.randrange(height), random.randrange(width)))
        elif ch == ord("c"):
            life.live_cells.clear()
        elif ch in (ord("-"), ord("_")):
            speed = max(1.0, speed / 2)
        elif ch in (ord("+"), ord("=")):
            speed = min(120.0, speed * 2)
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, _ = curses.getmouse()
            except curses.error:
                continue
            row, col = my - _BOARD_OFFSET, mx
            if 0 <= row < life.height and 0 <= col < life.width:
                cell = (row, col)
                if cell in life.live_cells:
                    life.live_cells.discard(cell)
                else:
                    life.live_cells.add(cell)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="game_of_life",
        description="Conway's Game of Life in your terminal.",
    )
    parser.add_argument("--pattern", choices=sorted(_PATTERNS), default="glider",
                        help="initial pattern (default: glider)")
    args = parser.parse_args(argv)
    try:
        curses.wrapper(_run, args)
    except KeyboardInterrupt:
        pass
    return 0
