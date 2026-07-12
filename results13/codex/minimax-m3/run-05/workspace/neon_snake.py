#!/usr/bin/env python3
"""Neon Snake — a tron-styled snake for the terminal.

Pure Python 3 stdlib (curses). No dependencies.

Controls
  Arrow keys / hjkl / WASD : steer
  q or Ctrl-C              : quit
  p                        : pause
  r                        : restart after game over

The grid wraps around its edges. Eat the glowing orbs to grow and rack up
a combo multiplier. Walls of the arena shimmer in shifting hues and the
snake's trail fades over time like a tron light cycle.
"""
from __future__ import annotations

import curses
import random
import time
from collections import deque
from dataclasses import dataclass, field

# Directions encoded as (dy, dx) deltas.
DIRS = {
    curses.KEY_UP:    (-1,  0),
    curses.KEY_DOWN:  ( 1,  0),
    curses.KEY_LEFT:  ( 0, -1),
    curses.KEY_RIGHT: ( 0,  1),
    ord('w'): (-1,  0), ord('W'): (-1,  0),
    ord('s'): ( 1,  0), ord('S'): ( 1,  0),
    ord('a'): ( 0, -1), ord('A'): ( 0, -1),
    ord('d'): ( 0,  1), ord('D'): ( 0,  1),
    ord('h'): ( 0, -1), ord('H'): ( 0, -1),
    ord('j'): ( 1,  0), ord('J'): ( 1,  0),
    ord('k'): (-1,  0), ord('K'): (-1,  0),
    ord('l'): ( 0,  1), ord('L'): ( 0,  1),
}

OPPOSITE = {
    (-1,  0): ( 1,  0),
    ( 1,  0): (-1,  0),
    ( 0, -1): ( 0,  1),
    ( 0,  1): ( 0, -1),
}

# Trail fade: each cell on the board holds a 'heat' that decays each tick.
HEAT_MAX = 8

COLOR_PAIRS = [
    (curses.COLOR_CYAN,    -1),  # 1 head / fresh trail
    (curses.COLOR_GREEN,   -1),  # 2 trail mid
    (curses.COLOR_BLUE,    -1),  # 3 trail old
    (curses.COLOR_MAGENTA, -1),  # 4 orb 1
    (curses.COLOR_YELLOW,  -1),  # 5 orb 2
    (curses.COLOR_RED,     -1),  # 6 orb 3
    (curses.COLOR_WHITE,   -1),  # 7 hud
    (curses.COLOR_BLACK,   curses.COLOR_CYAN),  # 8 selected menu
]


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    for i, (fg, bg) in enumerate(COLOR_PAIRS, start=1):
        try:
            curses.init_pair(i, fg, bg)
        except curses.error:
            pass


@dataclass
class Game:
    height: int
    width: int
    snake: deque = field(default_factory=deque)
    direction: tuple = (0, 1)
    pending_dir: tuple = (0, 1)
    heat: list = field(default_factory=list)
    orbs: list = field(default_factory=list)
    score: int = 0
    combo: int = 0
    combo_timer: float = 0.0
    speed: float = 0.10
    min_speed: float = 0.045
    alive: bool = True
    paused: bool = False
    over: bool = False
    ticks: int = 0
    flash: float = 0.0

    @classmethod
    def new(cls, height: int, width: int) -> "Game":
        g = cls(height=height, width=width)
        g.heat = [[0] * width for _ in range(height)]
        cy, cx = height // 2, width // 2
        g.snake = deque([(cy, cx - i) for i in range(4)])
        g.spawn_orb()
        g.spawn_orb()
        return g

    def spawn_orb(self) -> None:
        body = set(self.snake)
        taken = body | {(oy, ox) for oy, ox, _ in self.orbs}
        free = [(y, x) for y in range(self.height) for x in range(self.width)
                if (y, x) not in taken]
        if not free:
            return
        y, x = random.choice(free)
        kind = random.choice((0, 1, 2))
        self.orbs.append((y, x, kind))

    def step(self) -> None:
        if not self.alive or self.paused or self.over:
            return
        self.ticks += 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo = 0
        nd = self.pending_dir
        if nd != OPPOSITE.get(self.direction):
            self.direction = nd

        head_y, head_x = self.snake[0]
        dy, dx = self.direction
        ny = (head_y + dy) % self.height
        nx = (head_x + dx) % self.width

        if self.heat[ny][nx] >= HEAT_MAX - 1:
            self.alive = False
            self.over = True
            return

        py, px = self.snake[0]
        self.heat[py][px] = HEAT_MAX

        ate = None
        for i, (oy, ox, kind) in enumerate(self.orbs):
            if (ny, nx) == (oy, ox):
                ate = i
                break

        self.snake.appendleft((ny, nx))
        if ate is None:
            tail_y, tail_x = self.snake.pop()
            self.heat[tail_y][tail_x] = 0
        else:
            kind = self.orbs.pop(ate)[2]
            self.combo += 1
            self.combo_timer = 30
            base = [3, 5, 8][kind]
            gained = base * max(1, self.combo)
            self.score += gained
            self.flash = 1.0
            self.speed = max(self.min_speed, self.speed * 0.965)
            self.spawn_orb()

        for y in range(self.height):
            row = self.heat[y]
            for x in range(self.width):
                if row[x] > 0:
                    row[x] -= 1
        for (y, x) in self.snake:
            if self.heat[y][x] < HEAT_MAX - 2:
                self.heat[y][x] = HEAT_MAX - 2

    def steer(self, key: int) -> bool:
        if key in (ord('q'), ord('Q')):
            return True
        if key == ord('p') and not self.over:
            self.paused = not self.paused
            return False
        if key in DIRS:
            d = DIRS[key]
            if d != OPPOSITE.get(self.direction):
                self.pending_dir = d
        return False


def color_for_heat(h: int) -> int:
    if h >= 6:
        return 1
    if h >= 3:
        return 2
    if h >= 1:
        return 3
    return 0


def color_for_orb(kind: int) -> int:
    return 4 + kind


def draw_border(win, t: float) -> None:
    h, w = win.getmaxyx()
    phases = "-=-="
    ch_top = phases[int(t * 8) % len(phases)]
    for x in range(w - 1):
        try:
            win.addch(0, x, ch_top, curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass
    for x in range(w - 1):
        try:
            win.addch(h - 1, x, ch_top, curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass
    for y in range(1, h - 1):
        try:
            win.addch(y, 0, '|', curses.color_pair(1) | curses.A_DIM)
            win.addch(y, w - 1, '|', curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass


def draw_hud(win, game: Game) -> None:
    h, w = win.getmaxyx()
    combo = f"x{game.combo}" if game.combo > 1 else ""
    speed_pct = int(100 * (0.10 - game.speed) / (0.10 - game.min_speed))
    hud = f" SCORE {game.score:>6}   LEN {len(game.snake):>3}   SPD {speed_pct:>3}%   {combo} "
    try:
        win.addnstr(0, 2, hud.ljust(w - 4), w - 4, curses.color_pair(7) | curses.A_BOLD)
    except curses.error:
        pass


def draw_board(win, game: Game) -> None:
    flash_attr = curses.A_BOLD if game.flash > 0 else 0
    for (oy, ox, kind) in game.orbs:
        glyph = "o*+".replace('o', 'o')[kind] if False else ["o", "*", "+"][kind]
        try:
            win.addch(1 + oy, 1 + ox, glyph, curses.color_pair(color_for_orb(kind)) | curses.A_BOLD | flash_attr)
        except curses.error:
            pass

    for y in range(game.height):
        for x in range(game.width):
            hv = game.heat[y][x]
            if hv <= 0:
                continue
            cp = color_for_heat(hv)
            attr = curses.color_pair(cp) | (curses.A_BOLD if hv >= 6 else 0)
            ch = "#" if hv >= 5 else ("o" if hv >= 3 else ".")
            try:
                win.addch(1 + y, 1 + x, ch, attr)
            except curses.error:
                pass

    for i, (y, x) in enumerate(game.snake):
        try:
            if i == 0:
                dy, dx = game.direction
                arrow = {(-1,0):'^',(1,0):'v',(0,-1):'<',(0,1):'>'}[(dy, dx)]
                win.addch(1 + y, 1 + x, arrow, curses.color_pair(1) | curses.A_BOLD)
            else:
                win.addch(1 + y, 1 + x, "O", curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

    if game.flash > 0:
        game.flash = max(0.0, game.flash - 0.15)


def draw_overlay(win, lines) -> None:
    h, w = win.getmaxyx()
    max_len = max(len(s) for s, _ in lines)
    bw = max_len + 6
    bh = len(lines) + 4
    by = max(1, (h - bh) // 2)
    bx = max(1, (w - bw) // 2)
    try:
        for i, (text, cp) in enumerate(lines):
            win.addnstr(by + 2 + i, bx + 3, text.ljust(max_len), max_len, curses.color_pair(cp) | curses.A_BOLD)
        win.addnstr(by + 1, bx, "+" + "-" * (bw - 2) + "+", bw, curses.color_pair(1) | curses.A_BOLD)
        win.addnstr(by + bh - 2, bx, "+" + "-" * (bw - 2) + "+", bw, curses.color_pair(1) | curses.A_BOLD)
        for y in range(by + 2, by + bh - 2):
            win.addch(y, bx, "|", curses.color_pair(1) | curses.A_BOLD)
            win.addch(y, bx + bw - 1, "|", curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass


def main(stdscr) -> int:
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    sh, sw = stdscr.getmaxyx()
    height = max(10, sh - 2)
    width = max(20, sw - 2)
    game = Game.new(height, width)
    win = stdscr

    last_tick = time.monotonic()
    start = last_tick
    while True:
        now = time.monotonic()
        try:
            key = win.getch()
        except curses.error:
            key = -1
        if key != -1:
            if game.over and key in (ord('r'), ord('R')):
                game = Game.new(height, width)
                last_tick = now
                continue
            if game.steer(key):
                break

        if now - last_tick >= game.speed and not game.paused and not game.over:
            game.step()
            last_tick = now

        win.erase()
        draw_border(win, now - start)
        draw_board(win, game)
        draw_hud(win, game)
        if game.paused and not game.over:
            draw_overlay(win, [("  PAUSED  ", 7), ("  press p to resume  ", 1)])
        if game.over:
            draw_overlay(win, [
                ("  GAME OVER  ", 6),
                (f"  score: {game.score}  ", 7),
                (f"  length: {len(game.snake)}  ", 2),
                ("  press r to restart  ", 1),
                ("  press q to quit  ", 3),
            ])
        win.refresh()
        time.sleep(0.005)

    return 0


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
