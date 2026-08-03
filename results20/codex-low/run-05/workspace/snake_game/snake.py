#!/usr/bin/env python3
"""A retro terminal Snake game built with only the Python standard library.

Controls:
  Arrow keys / WASD  - steer the snake
  P                 - pause / resume
  R                 - restart after game over
  Q                 - quit (also at menu / pause)
  Enter / Space     - confirm at menus
"""

import curses
import random
import sys
import time

# ---------------------------------------------------------------------------
# Configuration / constants
# ---------------------------------------------------------------------------
FPS = {
    "Easy":   8.0,
    "Normal": 12.0,
    "Hard":   18.0,
}


class Direction:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    OPPOSITE = {
        UP: DOWN,
        DOWN: UP,
        LEFT: RIGHT,
        RIGHT: LEFT,
    }


# Terminal color pairs.
PAIR_FG = 1      # score / borders
PAIR_SNAKE = 2
PAIR_HEAD = 3
PAIR_FOOD = 4
PAIR_TEXT = 5
PAIR_TITLE = 6


def opposite(direction):
    return Direction.OPPOSITE[direction]


def rand_food(snake, cols, rows, min_y, max_y):
    """Pick a free cell for food."""
    occupied = set(snake)
    while True:
        x = random.randint(1, cols - 2)
        y = random.randint(min_y, max_y)
        if (x, y) not in occupied:
            return x, y


def center_text(width, text):
    return max(0, (width - len(text)) // 2)


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, stdscr, difficulty="Normal"):
        self.stdscr = stdscr
        self.difficulty = difficulty
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        self._init_colors()

        h, w = stdscr.getmaxyx()
        self.cols = w
        self.rows = h

        # Play area: keep one row for status, one for footer.
        self.min_y = 2
        self.max_y = h - 3

        self.reset()
        self.total_score = 0
        self.best_score = 0

    def _init_colors(self):
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(PAIR_FG, curses.COLOR_WHITE, -1)
        curses.init_pair(PAIR_SNAKE, curses.COLOR_GREEN, -1)
        curses.init_pair(PAIR_HEAD, curses.COLOR_YELLOW, -1)
        curses.init_pair(PAIR_FOOD, curses.COLOR_RED, -1)
        curses.init_pair(PAIR_TEXT, curses.COLOR_CYAN, -1)
        curses.init_pair(PAIR_TITLE, curses.COLOR_MAGENTA, -1)

    def reset(self):
        mid_x = self.cols // 2
        mid_y = (self.min_y + self.max_y) // 2
        self.snake = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y),
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food = rand_food(self.snake, self.cols, self.rows, self.min_y, self.max_y)
        self.score = 0
        self.paused = False
        self.over = False
        self.tick = time.time()

    # -- helpers -----------------------------------------------------------
    def status_line(self):
        return (
            f" Snake  |  Score: {self.score:>4}   Best: {self.best_score:>4}"
            f"   Speed: {self.difficulty}"
        )

    # -- input -------------------------------------------------------------
    def handle_key(self, key):
        moves = {
            ord("w"), ord("W"), curses.KEY_UP,
            ord("s"), ord("S"), curses.KEY_DOWN,
            ord("a"), ord("A"), curses.KEY_LEFT,
            ord("d"), ord("D"), curses.KEY_RIGHT,
        }

        if key in (ord("q"), ord("Q"), 27):  # Q or ESC
            return "quit"

        if self.over:
            if key in (ord("r"), ord("R")):
                self.reset()
            return None

        if key in (ord("p"), ord("P")):
            self.paused = not self.paused
            self.tick = time.time()
            return None

        direction = None
        if key in (ord("w"), ord("W"), curses.KEY_UP):
            direction = Direction.UP
        elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
            direction = Direction.DOWN
        elif key in (ord("a"), ord("A"), curses.KEY_LEFT):
            direction = Direction.LEFT
        elif key in (ord("d"), ord("D"), curses.KEY_RIGHT):
            direction = Direction.RIGHT

        if direction and direction != opposite(self.direction):
            self.next_direction = direction

        if key in moves and self.paused:
            return None
        return None

    # -- update ------------------------------------------------------------
    def step(self):
        if self.over or self.paused:
            return

        self.direction = self.next_direction
        dx, dy = self.direction
        head = self.snake[0]
        new_head = (head[0] + dx, head[1] + dy)

        # Eat food?
        ate = new_head == self.food

        # Collision with self (ignore the tail cell we're about to vacate).
        body = self.snake[:-1] if not ate else self.snake
        hit_self = new_head in body

        # Collision with walls / out of bounds.
        x, y = new_head
        out_of_bounds = (
            x <= 0 or x >= self.cols - 1 or
            y < self.min_y or y > self.max_y
        )

        if hit_self or out_of_bounds:
            self.over = True
            self.best_score = max(self.best_score, self.score)
            return

        self.snake.insert(0, new_head)
        if ate:
            self.score += 1
            self.best_score = max(self.best_score, self.score)
            self.food = rand_food(self.snake, self.cols, self.rows, self.min_y, self.max_y)
        else:
            self.snake.pop()

    # -- rendering ---------------------------------------------------------
    def draw(self):
        stdscr = self.stdscr
        stdscr.erase()

        # Border around the whole screen.
        try:
            stdscr.border()
        except curses.error:
            pass

        # Status line.
        stdscr.addstr(1, 2, self.status_line(), curses.color_pair(PAIR_FG))

        # Food.
        fx, fy = self.food
        try:
            stdscr.addstr(fy, fx, "@", curses.color_pair(PAIR_FOOD))
        except curses.error:
            pass

        # Snake body.
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                ch, pair = "O", PAIR_HEAD
            else:
                ch, pair = "o", PAIR_SNAKE
            try:
                stdscr.addstr(y, x, ch, curses.color_pair(pair))
            except curses.error:
                pass

        # Footer.
        footer = " Arrows/WASD: move   P: pause   Q: quit "
        stdscr.addstr(self.rows - 1, center_text(self.cols, footer), footer,
                      curses.color_pair(PAIR_TEXT))

        self._draw_overlay(stdscr)
        stdscr.refresh()

    def _draw_overlay(self, stdscr):
        if self.paused and not self.over:
            self._draw_box(
                stdscr,
                ["  PAUSED  ", "  P: resume   Q: quit  "],
                curses.color_pair(PAIR_TEXT),
            )
        elif self.over:
            lines = [
                " GAME OVER ",
                f" Score: {self.score}   Best: {self.best_score} ",
                "  R: restart   Q: quit  ",
            ]
            self._draw_box(stdscr, lines, curses.color_pair(PAIR_TITLE))

    def _draw_box(self, stdscr, lines, pair):
        width = max(len(l) for l in lines) + 4
        height = len(lines) + 2
        top = max(1, (self.rows - height) // 2)
        left = max(1, (self.cols - width) // 2)
        try:
            for i, line in enumerate(lines):
                stdscr.addstr(top + 1 + i, left + 2, line, pair)
            for j in range(height):
                stdscr.addstr(top + j, left, " " * width, curses.color_pair(PAIR_FG))
            stdscr.addstr(top, left - 1, " " * (width + 2))
            stdscr.refresh()
        except curses.error:
            pass


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------
def draw_pause_cover(stdscr, msg):
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    text = msg
    stdscr.addstr(h // 2, center_text(w, text), text, curses.color_pair(PAIR_TITLE))


def menu(stdscr, title, options, selected):
    """Generic single-line-menu. Returns chosen index or None on quit."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)
    h, w = stdscr.getmaxyx()

    while True:
        stdscr.erase()
        try:
            stdscr.border()
        except curses.error:
            pass

        stdscr.addstr(h // 2 - 3, center_text(w, title), title,
                      curses.color_pair(PAIR_TITLE) | curses.A_BOLD)

        for i, opt in enumerate(options):
            y = h // 2 - 1 + i
            if i == selected:
                prefix = "> "
                style = curses.color_pair(PAIR_FOOD) | curses.A_BOLD
            else:
                prefix = "  "
                style = curses.color_pair(PAIR_TEXT)
            stdscr.addstr(y, center_text(w, prefix + opt), prefix + opt, style)

        hint = " Use Up/Down + Enter to select   Q: quit "
        stdscr.addstr(h - 2, center_text(w, hint), hint, curses.color_pair(PAIR_FG))
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("w"), ord("W"), ord("k"), ord("K")):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("s"), ord("S"), ord("j"), ord("J")):
            selected = (selected + 1) % len(options)
        elif key in (10, 13, ord(" ")):  # Enter / Space
            return selected
        elif key in (ord("q"), ord("Q"), 27):
            return None


def main(stdscr):
    random.seed()

    difficulties = list(FPS.keys())
    game = Game(stdscr, difficulty="Normal")
    title = " ~ S N A K E ~ "

    # Main menu: Play / Difficulty / Quit
    main_items = ["Play", "Difficulty", "Quit"]
    diff_idx = difficulties.index("Normal")
    sel = 0

    while True:
        choice = menu(stdscr, title, main_items, sel)
        if choice is None or choice == 2:
            return  # quit

        if choice == 0:  # Play
            game.difficulty = difficulties[diff_idx]
            game.reset()
            run_game(stdscr, game)
            # after game loop, return to main menu
            continue

        if choice == 1:  # Difficulty
            diff_choice = menu(stdscr, f"{title}  -  Difficulty",
                               difficulties, diff_idx)
            if diff_choice is not None:
                diff_idx = diff_choice
                game.difficulty = difficulties[diff_idx]
            sel = 1


def run_game(stdscr, game):
    stdscr.nodelay(True)

    while True:
        key = stdscr.getch()
        if key == -1:
            key = 0
        result = game.handle_key(key)
        if result == "quit":
            return

        # Tick at the configured speed.
        now = time.time()
        interval = 1.0 / FPS[game.difficulty]
        if now - game.tick >= interval:
            game.step()
            game.tick = now

        game.draw()
        time.sleep(0.004)


def run():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nBye!")
    except Exception as exc:  # pragma: no cover - defence in depth
        print(f"\nError: {exc}", file=sys.stderr)
    finally:
        pass


if __name__ == "__main__":
    run()
