#!/usr/bin/env python3
"""Terminal Snake game built with curses.

Controls:
    Arrow keys or WASD  - move
    P                   - pause
    R                   - restart after game over
    Q                   - quit
"""
from __future__ import annotations

import curses
import json
import os
import random
import time
from pathlib import Path

SCORE_FILE = Path.home() / ".snake_scores.json"


def load_high_scores() -> dict[str, int]:
    try:
        return json.loads(SCORE_FILE.read_text())
    except Exception:
        return {"easy": 0, "normal": 0, "hard": 0}


def save_high_scores(scores: dict[str, int]) -> None:
    try:
        SCORE_FILE.write_text(json.dumps(scores, indent=2))
    except Exception:
        pass


DIFFICULTIES = {
    "easy": {"base_delay": 0.14, "min_delay": 0.05, "accel": 0.004, "grow_every": 2},
    "normal": {"base_delay": 0.09, "min_delay": 0.04, "accel": 0.003, "grow_every": 2},
    "hard": {"base_delay": 0.06, "min_delay": 0.03, "accel": 0.0025, "grow_every": 1},
}

UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

OPPOSITES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def pick_food(snake: list[tuple[int, int]], rows: int, cols: int) -> tuple[int, int]:
    occupied = set(snake)
    while True:
        cell = (random.randint(1, rows - 2), random.randint(1, cols - 2))
        if cell not in occupied:
            return cell


def draw_border(win: curses.window, rows: int, cols: int, color: int) -> None:
    win.attron(color)
    win.hline(0, 1, curses.ACS_HLINE, cols - 2)
    win.hline(rows - 1, 1, curses.ACS_HLINE, cols - 2)
    win.vline(1, 0, curses.ACS_VLINE, rows - 2)
    win.vline(1, cols - 1, curses.ACS_VLINE, rows - 2)
    win.addch(0, 0, curses.ACS_ULCORNER)
    win.addch(0, cols - 1, curses.ACS_URCORNER)
    win.addch(rows - 1, 0, curses.ACS_LLCORNER)
    win.addch(rows - 1, cols - 1, curses.ACS_LRCORNER)
    win.attroff(color)


def draw_snake(win: curses.window, snake: list[tuple[int, int]], head_color: int, body_color: int) -> None:
    for i, (r, c) in enumerate(snake):
        try:
            if i == 0:
                win.addch(r, c, "@", head_color | curses.A_BOLD)
            else:
                win.addch(r, c, "o", body_color)
        except curses.error:
            pass


def show_menu(stdscr: curses.window) -> tuple[str, int, int]:
    curses.curs_set(0)
    stdscr.clear()
    rows, cols = stdscr.getmaxyx()
    title = "S N A K E"
    sub = "Pick a difficulty (1/2/3), then press ENTER"
    options = ["1) Easy", "2) Normal", "3) Hard"]
    scores = load_high_scores()

    start_r = max(2, rows // 2 - 5)
    try:
        stdscr.addstr(start_r, max(0, (cols - len(title)) // 2), title,
                      curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(start_r + 2, max(0, (cols - len(sub)) // 2), sub, curses.color_pair(2))
        for i, opt in enumerate(options):
            stdscr.addstr(start_r + 4 + i, max(0, (cols - len(opt)) // 2), opt,
                          curses.color_pair(3) | curses.A_BOLD)
        hint = "High scores -> Easy: {easy}  Normal: {normal}  Hard: {hard}".format(**scores)
        stdscr.addstr(start_r + 8, max(0, (cols - len(hint)) // 2), hint, curses.color_pair(5))
        quit_hint = "Press Q at any time to quit"
        stdscr.addstr(rows - 2, max(0, (cols - len(quit_hint)) // 2), quit_hint, curses.color_pair(6))
    except curses.error:
        pass
    stdscr.refresh()

    selection = 1
    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            raise SystemExit(0)
        if key in (ord("1"), ord("2"), ord("3")):
            selection = key - ord("0")
        if key in (curses.KEY_BACKSPACE, ord("\n"), curses.KEY_ENTER):
            break

    difficulty = ["easy", "normal", "hard"][selection - 1]
    play_rows = max(15, min(rows - 3, 30))
    play_cols = max(30, min(cols - 2, 80))
    # Ensure even dims so border math behaves.
    if play_cols % 2:
        play_cols -= 1
    return difficulty, play_rows, play_cols


def run_game(stdscr: curses.window, difficulty: str, rows: int, cols: int) -> tuple[int, bool]:
    """Returns (final_score, wants_restart)."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(20)

    cfg = DIFFICULTIES[difficulty]
    start_r, start_c = rows // 2, cols // 2
    snake = [(start_r, start_c - i) for i in range(3)]
    direction = RIGHT
    food = pick_food(snake, rows, cols)
    score = 0
    eaten_since_growth = 0
    delay = cfg["base_delay"]
    last_tick = time.monotonic()
    paused = False

    border_pair = curses.color_pair(2)
    head_pair = curses.color_pair(4)
    body_pair = curses.color_pair(3)
    food_pair = curses.color_pair(5) | curses.A_BOLD
    hud_pair = curses.color_pair(6) | curses.A_BOLD

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            raise SystemExit(0)
        if key in (ord("p"), ord("P")):
            paused = not paused
        if paused and key not in (ord("p"), ord("P"), ord("q"), ord("Q")):
            continue

        new_dir = None
        if key in (curses.KEY_UP, ord("w"), ord("W")):
            new_dir = UP
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            new_dir = DOWN
        elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
            new_dir = LEFT
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            new_dir = RIGHT
        if new_dir and new_dir != OPPOSITES.get(direction):
            direction = new_dir

        now = time.monotonic()
        if not paused and now - last_tick >= delay:
            last_tick = now
            head = snake[0]
            new_head = (head[0] + direction[0], head[1] + direction[1])

            # Collision with walls.
            if not (1 <= new_head[0] <= rows - 2 and 1 <= new_head[1] <= cols - 2):
                return score, False
            # Collision with self.
            if new_head in snake[:-1]:
                return score, False

            snake.insert(0, new_head)
            if new_head == food:
                score += 10 + (5 * (len(snake) // 3))
                eaten_since_growth += 1
                if eaten_since_growth >= cfg["grow_every"]:
                    eaten_since_growth = 0
                else:
                    snake.pop()
                food = pick_food(snake, rows, cols)
                delay = max(cfg["min_delay"], delay - cfg["accel"])
            else:
                snake.pop()

        # Draw.
        stdscr.erase()
        try:
            draw_border(stdscr, rows, cols, border_pair)
            stdscr.addch(food[0], food[1], "*", food_pair)
            draw_snake(stdscr, snake, head_pair, body_pair)

            hud = f" Score: {score} | Length: {len(snake)} | {difficulty.upper()} | P=pause "
            stdscr.addstr(0, max(0, (cols - len(hud)) // 2), hud, hud_pair)
            if paused:
                msg = " PAUSED — press P to resume "
                stdscr.addstr(rows - 1, max(0, (cols - len(msg)) // 2), msg,
                              curses.color_pair(5) | curses.A_BOLD | curses.A_REVERSE)
        except curses.error:
            pass
        stdscr.refresh()


def show_game_over(stdscr: curses.window, score: int, difficulty: str, new_high: bool) -> bool:
    """Returns True if the player wants to restart."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.clear()
    rows, cols = stdscr.getmaxyx()
    title = "G A M E   O V E R"
    line1 = f"Final score: {score}"
    line2 = "NEW HIGH SCORE!" if new_high else "Try again? You know you want to."
    prompt = "R = restart   |   M = menu   |   Q = quit"

    r = max(2, rows // 2 - 3)
    try:
        stdscr.addstr(r, max(0, (cols - len(title)) // 2), title,
                      curses.color_pair(5) | curses.A_BOLD)
        stdscr.addstr(r + 2, max(0, (cols - len(line1)) // 2), line1,
                      curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(r + 3, max(0, (cols - len(line2)) // 2), line2,
                      curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(r + 5, max(0, (cols - len(prompt)) // 2), prompt,
                      curses.color_pair(3))
    except curses.error:
        pass
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord("r"), ord("R")):
            return True
        if key in (ord("m"), ord("M")):
            return False
        if key in (ord("q"), ord("Q")):
            raise SystemExit(0)


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)


def main(stdscr: curses.window) -> None:
    init_colors()
    scores = load_high_scores()
    while True:
        difficulty, rows, cols = show_menu(stdscr)
        setup = curses.newwin(rows, cols, 0, 0)
        final_score = 0
        while True:
            final_score, _wants_restart = run_game(setup, difficulty, rows, cols)
            new_high = final_score > scores.get(difficulty, 0)
            if new_high:
                scores[difficulty] = final_score
                save_high_scores(scores)
            if not show_game_over(setup, final_score, difficulty, new_high):
                break


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
