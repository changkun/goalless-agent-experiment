"""Curses-based terminal interface for Snake."""

from __future__ import annotations

import curses
import time

from snake_game.core import Direction, Game, Status


def _draw(stdscr, game) -> None:
    height, width = stdscr.getmaxyx()

    score_text = f"Score: {game.score}   Steps: {game.steps}"
    stdscr.addnstr(0, 0, score_text, width)
    stdscr.addnstr(1, 0, "Arrows/WASD move | q quit | p pause", width)

    pad_x = 2
    pad_y = 3

    for y in range(game.height):
        for x in range(game.width):
            ch = " "
            if game.food is not None and (x, y) == (game.food.x, game.food.y):
                ch = "@"
            for i, cell in enumerate(game.snake):
                if (cell.x, cell.y) == (x, y):
                    ch = "O" if i == 0 else "o"
                    break
            try:
                stdscr.addch(pad_y + y, pad_x + x, ch)
            except curses.error:
                pass

    status_line = f"Status: {game.status.value}"
    if game.status is Status.WON:
        status_line += "  -- You won! (q to quit)"
    elif game.status is Status.CRASHED:
        status_line += "  -- Game over! (r to restart, q to quit)"
    try:
        stdscr.addnstr(pad_y + game.height + 1, 0, status_line, width)
    except curses.error:
        pass
    stdscr.refresh()


def _run_loop(stdscr, game) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    paused = False
    while True:
        _draw(stdscr, game)

        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q")):
                break
            direction = None
            if key in (curses.KEY_UP, ord("w"), ord("W")):
                direction = Direction.UP
            elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
                direction = Direction.DOWN
            elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
                direction = Direction.LEFT
            elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
                direction = Direction.RIGHT
            elif key in (ord("p"), ord("P")):
                paused = not paused
            elif key in (ord("r"), ord("R")) and game.status in (Status.WON, Status.CRASHED):
                game.__init__(game.width, game.height)

            if direction is not None:
                game.try_turn(direction)

        if not paused and game.status is Status.RUNNING:
            game.step()

        if paused:
            time.sleep(0.05)
        else:
            time.sleep(0.1)


def play(width: int = 20, height: int = 10, seed=None) -> None:
    curses.wrapper(_run_loop, Game(width, height, seed))
