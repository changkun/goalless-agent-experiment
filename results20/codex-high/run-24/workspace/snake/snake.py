#!/usr/bin/env python3
"""Retro Snake — a single-file curses game with a persistent scoreboard."""

import curses
import os
import random
import tempfile
from collections import deque

TITLE = "SNEK"
MENU = ["Play", "High Scores", "Quit"]
MIN_DELAY = 0.045
MAX_DELAY = 0.16
SPEED_STEP = 0.005
FOOD_TO_NEXT = 4
MAX_HISCORES = 5


def score_path():
    env = os.environ.get("XDG_DATA_HOME", "").strip()
    candidates = []
    if env:
        candidates.append(os.path.join(env, "snek_scores.txt"))
    candidates.append(os.path.join(os.path.expanduser("~"), ".snek_scores.txt"))
    candidates.append(os.path.join(tempfile.gettempdir(), "snek_scores.txt"))
    for c in candidates:
        try:
            with open(c, "a"):
                pass
            return c
        except OSError:
            continue
    return candidates[-1]


def load_scores():
    scores = []
    try:
        with open(score_path()) as fh:
            for line in fh:
                line = line.strip()
                try:
                    scores.append(int(line))
                except ValueError:
                    continue
    except OSError:
        return []
    scores.sort(reverse=True)
    return scores[:MAX_HISCORES]


def save_score(value):
    try:
        with open(score_path(), "a") as fh:
            fh.write(f"{value}\n")
    except OSError:
        pass


class Game:
    PAD = 2

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def run(self):
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        try:
            self.stdscr.keypad(True)
        except curses.error:
            pass
        if curses.has_colors():
            try:
                curses.start_color()
            except curses.error:
                pass
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
        while True:
            self.stdscr.erase()
            choice = self.menu()
            if choice == 0:
                self.play_round()
            elif choice == 1:
                self.scores_screen()
            else:
                return

    def center(self, text, y, attr=0):
        h, w = self.stdscr.getmaxyx()
        x = max(0, (w - len(text)) // 2)
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def menu(self):
        selected = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title_y = max(0, h // 2 - 5)
            self.center(TITLE, title_y, curses.color_pair(1) | curses.A_BOLD)
            for i, label in enumerate(MENU):
                y = title_y + 4 + i * 2
                prefix = "> " if i == selected else "  "
                attr = curses.A_REVERSE if i == selected else curses.color_pair(2)
                self.stdscr.addstr(y, max(0, (w - len(label)) // 2 - 2), prefix + label, attr)
            hint = "Arrows/WASD to move  P to pause  Q to quit"
            self.center(hint, h - 1, curses.A_DIM)
            if w < 40 or h < 14:
                self.center("Window too small — make it at least 40x14", h - 2, curses.color_pair(3))
            self.stdscr.refresh()
            key = self.stdscr.getkey()
            if key in ("KEY_UP", "k"):
                selected = (selected - 1) % len(MENU)
            elif key in ("KEY_DOWN", "j"):
                selected = (selected + 1) % len(MENU)
            elif key in ("\n", "\r", " "):
                return selected
            elif key in ("q", "Q"):
                return 2

    def scores_screen(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        self.center("HIGH SCORES", max(0, h // 2 - 5), curses.color_pair(1) | curses.A_BOLD)
        scores = load_scores()
        if not scores:
            self.center("No scores yet — go play!", h // 2, curses.A_DIM)
        else:
            for i, s in enumerate(scores, 1):
                rank = "1st" if i == 1 else ("2nd" if i == 2 else ("3rd" if i == 3 else f"{i}th"))
                self.center(f"{rank:>3}  {s}", h // 2 - 2 + i, curses.color_pair(2))
        self.center("Press any key to return", h - 1, curses.A_DIM)
        self.stdscr.refresh()
        self.stdscr.getkey()

    def pause(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.nodelay(False)
        self.stdscr.erase()
        self.center("PAUSED", h // 2 - 1, curses.color_pair(1) | curses.A_BOLD)
        self.center("Press P or Space to resume", h // 2 + 1, curses.A_DIM)
        self.stdscr.refresh()
        while True:
            try:
                key = self.stdscr.getkey()
            except curses.error:
                continue
            if key in ("p", "P", " ", "\n"):
                return

    def play_round(self):
        h, w = self.stdscr.getmaxyx()
        play_w = w - self.PAD * 2 - 2   # inner area inside border
        play_h = h - self.PAD * 2 - 2
        if play_h < 4 or play_w < 5:
            self.stdscr.erase()
            self.center("Window too small to play", h // 2, curses.color_pair(3))
            self.center("Enlarge the terminal and press any key", h // 2 + 1)
            self.stdscr.refresh()
            self.stdscr.getkey()
            return

        def px(x):
            return self.PAD + 1 + x

        def py(y):
            return self.PAD + 1 + y

        snake = deque([(play_w // 2, play_h // 2)])
        direction = (1, 0)
        delay = MAX_DELAY
        pieces = 0
        score = 0
        cells = play_w * play_h

        def free_positions():
            occupied = set(snake)
            return [(x, y) for y in range(play_h) for x in range(play_w)
                    if (x, y) not in occupied]

        def place_food():
            free = free_positions()
            return random.choice(free) if free else None

        food = place_food()
        self.stdscr.erase()
        try:
            self.stdscr.border(0)
        except curses.error:
            pass
        self.stdscr.timeout(int(delay * 1000))

        def draw():
            self.stdscr.move(0, 1)
            self.stdscr.clrtoeol()
            try:
                self.stdscr.addstr(0, 1, f"Score: {score}   Length: {len(snake)}",
                                   curses.color_pair(2))
            except curses.error:
                pass
            for x, y in snake:
                attr = curses.color_pair(1) if (x, y) == snake[0] else curses.color_pair(2)
                try:
                    self.stdscr.addch(py(y), px(x), "@", attr)
                except curses.error:
                    pass
            if food:
                try:
                    self.stdscr.addch(py(food[1]), px(food[0]), "*",
                                      curses.color_pair(4) | curses.A_BOLD)
                except curses.error:
                    pass
            self.stdscr.refresh()

        draw()
        while True:
            try:
                key = self.stdscr.getkey()
            except curses.error:
                key = None
            if key:
                if key in ("q", "Q"):
                    self.end_game(score)
                    return
                if key in ("p", "P", " "):
                    self.pause()
                    self.stdscr.timeout(int(delay * 1000))
                    draw()
                    continue
                new_dir = direction
                if key in ("KEY_UP", "k"):
                    new_dir = (0, -1)
                elif key in ("KEY_DOWN", "j"):
                    new_dir = (0, 1)
                elif key in ("KEY_LEFT", "h"):
                    new_dir = (-1, 0)
                elif key in ("KEY_RIGHT", "l"):
                    new_dir = (1, 0)
                if new_dir != (0, 0) and (new_dir[0], new_dir[1]) != (-direction[0], -direction[1]):
                    direction = new_dir

            head = snake[0]
            nhead = (head[0] + direction[0], head[1] + direction[1])
            if not (0 <= nhead[0] < play_w and 0 <= nhead[1] < play_h) or nhead in snake:
                self.end_game(score)
                return
            snake.appendleft(nhead)
            if nhead == food:
                score += 1
                pieces += 1
                if pieces % FOOD_TO_NEXT == 0:
                    delay = max(MIN_DELAY, delay - SPEED_STEP)
                    self.stdscr.timeout(int(delay * 1000))
                food = place_food()
            else:
                snake.pop()
            if len(snake) >= cells:
                self.end_game(score)
                return
            draw()

    def end_game(self, score):
        save_score(score)
        h, w = self.stdscr.getmaxyx()
        best = load_scores()
        is_best = best and score == best[0]
        self.stdscr.nodelay(False)
        self.stdscr.erase()
        self.center("GAME OVER", h // 2 - 3, curses.color_pair(3) | curses.A_BOLD)
        self.center(f"Score: {score}", h // 2, curses.color_pair(2))
        if best:
            self.center(f"Best: {best[0]}", h // 2 + 1, curses.A_DIM)
        if is_best:
            self.center("NEW HIGH SCORE!", h // 2 + 2, curses.color_pair(1) | curses.A_BOLD)
        self.center("Press any key for menu", h - 1, curses.A_DIM)
        self.stdscr.refresh()
        self.stdscr.getkey()


def main(stdscr):
    Game(stdscr).run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
