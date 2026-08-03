"""Curses terminal UI for the Game of Life."""

from __future__ import annotations

import curses
import time
from typing import Optional

from . import patterns
from .engine import World
from .patterns import load


class Game:
    """Holds the simulation state and view offset for the interactive loop."""

    def __init__(self) -> None:
        self.world = World()
        self.paused = True
        self.generation = 0
        self.speed = 8  # generations per second
        self.speed_idx = 4
        self.pattern_idx = 0
        self.view_x = 0
        self.view_y = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.pattern_names = patterns.names()

    # -- pattern management ------------------------------------------------
    def load_pattern(self, name: str) -> None:
        self.world.clear()
        self.generation = 0
        for x, y in load(name):
            self.world.set((x, y))


def _draw_grid(stdscr, game: Game, height: int, width: int) -> None:
    for y in range(height):
        row_y = game.view_y + y
        for x in range(width):
            cell_x = game.view_x + x
            if (cell_x, row_y) in game.world:
                try:
                    stdscr.addch(y, x, "█", curses.color_pair(1))
                except curses.error:
                    pass


def _draw_hud(stdscr, game: Game, width: int) -> None:
    name = game.pattern_names[game.pattern_idx]
    status = "PAUSED" if game.paused else "RUNNING"
    line = (
        f" gen {game.generation} | alive {game.world.alive} | "
        f"{status} | {game.speed} gen/s | pattern: {name}"
    )
    stdscr.move(0, 0)
    stdscr.clrtoeol()
    stdscr.addnstr(line, width - 1)


def run(stdscr) -> None:
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # live cells
    curses.init_pair(2, curses.COLOR_CYAN, -1)  # cursor highlight

    game = Game()
    game.load_pattern(game.pattern_names[0])
    stdscr.nodelay(True)
    stdscr.keypad(True)

    while True:
        height, width = stdscr.getmaxyx()
        grid_h = max(0, height - 1)
        grid_w = max(0, width)

        key = stdscr.getch()

        if key == ord("q"):
            break
        elif key == ord(" "):
            game.paused = not game.paused
        elif key == ord("s"):
            game.world.step_in_place()
            game.generation += 1
        elif key == ord("n"):
            game.pattern_idx = (game.pattern_idx + 1) % len(game.pattern_names)
            game.load_pattern(game.pattern_names[game.pattern_idx])
        elif key == ord("p"):
            game.pattern_idx = (game.pattern_idx - 1) % len(game.pattern_names)
            game.load_pattern(game.pattern_names[game.pattern_idx])
        elif key == ord("c"):
            game.world.clear()
            game.generation = 0
        elif key == ord("+"):
            _change_speed(game, +1)
        elif key == ord("-"):
            _change_speed(game, -1)
        elif key == ord("r"):
            game.view_x, game.view_y = 0, 0
        elif key == ord("o"):
            game.paused = True
            _center_pattern_origin(game)
        elif key == curses.KEY_UP:
            _pan(game, 0, -1)
        elif key == curses.KEY_DOWN:
            _pan(game, 0, 1)
        elif key == curses.KEY_LEFT:
            _pan(game, -1, 0)
        elif key == curses.KEY_RIGHT:
            _pan(game, 1, 0)
        elif key in (curses.KEY_ENTER, 10, 13):
            world_x = game.view_x + game.cursor_x
            world_y = game.view_y + game.cursor_y
            game.world.toggle((world_x, world_y))

        if not game.paused:
            game.world.step_in_place()
            game.generation += 1

        stdscr.erase()
        _draw_grid(stdscr, game, grid_h, grid_w)
        _draw_cursor(stdscr, game, grid_h, grid_w)
        _draw_hud(stdscr, game, width)
        stdscr.refresh()

        delay = max(0.02, 1.0 / game.speed)
        time.sleep(delay)


def _change_speed(game: Game, delta: int) -> None:
    levels = [1, 2, 4, 8, 15, 30, 60]
    game.speed_idx = max(0, min(len(levels) - 1, game.speed_idx + delta))
    game.speed = levels[game.speed_idx]


def _pan(game: Game, dx: int, dy: int) -> None:
    game.view_x += dx
    game.view_y += dy


def _center_pattern_origin(game: Game) -> None:
    seen = list(game.world.live)
    if not seen:
        return
    xs = [x for x, _ in seen]
    ys = [y for _, y in seen]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    game.view_x = -(min_x + max_x) // 2
    game.view_y = -(min_y + max_y) // 2


def _draw_cursor(stdscr, game: Game, height: int, width: int) -> None:
    sx, sy = game.cursor_x, game.cursor_y
    if 0 <= sx < width and 0 <= sy < height:
        try:
            stdscr.addch(sy, sx, "×", curses.color_pair(2))
        except curses.error:
            pass


def main() -> None:
    curses.wrapper(run)


if __name__ == "__main__":
    main()
