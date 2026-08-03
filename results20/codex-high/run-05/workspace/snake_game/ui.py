"""Curses-based terminal UI for the snake game."""

from __future__ import annotations

import curses
from typing import Optional

from .logic import DOWN, LEFT, RIGHT, UP, Game

# Key integer -> direction. Curses arrow keys plus WASD/arrow aliases handled
# via their integer codes; single characters via ord().
_ARROWS = {curses.KEY_UP: UP, curses.KEY_DOWN: DOWN, curses.KEY_LEFT: LEFT, curses.KEY_RIGHT: RIGHT}
_KEYS: dict[int, object] = {
    **_ARROWS,
    ord("w"): UP, ord("W"): UP,
    ord("s"): DOWN, ord("S"): DOWN,
    ord("a"): LEFT, ord("A"): LEFT,
    ord("d"): RIGHT, ord("D"): RIGHT,
}


def _draw(stdscr: curses.window, game: Game) -> None:
    h, w = stdscr.getmaxyx()
    ox = max(0, (w - game.width) // 2)
    oy = max(0, (h - game.height) // 2 - 1)

    title = "SNAKE"
    stdscr.addstr(max(0, oy - 1), ox + max(0, (game.width - len(title)) // 2), title, curses.A_BOLD)
    stdscr.addstr(oy + game.height + 1, ox, f"Score: {game.score}")

    for dx in range(game.width + 1):
        stdscr.addch(oy, ox + dx, curses.ACS_HLINE)
        stdscr.addch(oy + game.height + 1, ox + dx, curses.ACS_HLINE)
    for dy in range(game.height + 1):
        stdscr.addch(oy + dy, ox, curses.ACS_VLINE)
        stdscr.addch(oy + dy, ox + game.width + 1, curses.ACS_VLINE)
    for cy, cx in ((0, 0), (0, game.width), (game.height, 0), (game.height, game.width)):
        stdscr.addch(oy + cy, ox + cx, curses.ACS_ULCORNER if cy == 0 and cx == 0 else
                     curses.ACS_URCORNER if cy == 0 else
                     curses.ACS_LLCORNER if cx == 0 else curses.ACS_LRCORNER)

    fx, fy = game.food
    stdscr.addch(oy + 1 + fy, ox + 1 + fx, "@", curses.A_BOLD)

    for i, (sx, sy) in enumerate(game.cells):
        ch = "O" if i == 0 else "o"
        stdscr.addch(oy + 1 + sy, ox + 1 + sx, ch, curses.A_REVERSE if i == 0 else 0)

    stdscr.addstr(max(0, h - 1), 0, "Arrows/WASD move  Q quit")


def _draw_game_over(stdscr: curses.window, score: int) -> None:
    stdscr.nodelay(False)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    if score < 0:
        lines = ["Quit", "See you next time!"]
    else:
        lines = ["Game Over", f"Final score: {score}"]

    for i, line in enumerate(lines):
        stdscr.addstr(h // 2 - 1 + i, max(0, (w - len(line)) // 2), line, curses.A_BOLD if i == 0 else 0)

    prompt = "Press any key to exit"
    stdscr.addstr(h // 2 + 2, max(0, (w - len(prompt)) // 2), prompt)
    stdscr.refresh()
    stdscr.getch()


def run(stdscr: curses.window, width: int = 20, height: int = 20, seed: Optional[int] = None) -> int:
    """Run the game inside an active curses window; returns the final score."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    game = Game.new(width=width, height=height, seed=seed)
    pending: Optional[object] = None

    while True:
        stdscr.clear()
        _draw(stdscr, game)
        stdscr.refresh()

        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            _draw_game_over(stdscr, -1)
            return -1

        if key in _KEYS:
            pending = _KEYS[key]

        if not game.game_over:
            if pending is not None:
                game.turn(pending)
                pending = None
            game.step()

        if game.game_over:
            _draw_game_over(stdscr, game.score)
            return game.score

        curses.napms(90)
