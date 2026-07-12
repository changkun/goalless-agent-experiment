#!/usr/bin/env python3
"""
Matrix Rain — a smooth terminal cascade of falling katakana glyphs.

Run:  python3 matrix_rain.py
Quit: Ctrl+C
"""
import curses
import random
import time
import unicodedata

GLYPHS = [
    "ｱ", "ｲ", "ｳ", "ｴ", "ｵ", "ｶ", "ｷ", "ｸ", "ｹ", "ｺ",
    "ｻ", "ｼ", "ｽ", "ｾ", "ｿ", "ﾀ", "ﾁ", "ﾂ", "ﾃ", "ﾄ",
    "ﾅ", "ﾆ", "ﾇ", "ﾈ", "ﾉ", "ﾊ", "ﾋ", "ﾌ", "ﾍ", "ﾎ",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
]

class Stream:
    __slots__ = ("head", "speed", "trail", "glyphs")
    def __init__(self, height):
        self.height = height
        self.reset(height, top=False)

    def reset(self, height, top=True):
        self.head = -random.randint(0, height) if top else random.randint(-height, 0)
        self.speed = random.uniform(0.15, 0.45)
        self.trail = random.randint(8, 22)
        self.glyphs = [random.choice(GLYPHS) for _ in range(self.trail)]

    def step(self, dt):
        self.head += self.speed * dt
        if random.random() < 0.04:
            idx = random.randint(0, len(self.glyphs) - 1)
            self.glyphs[idx] = random.choice(GLYPHS)

class Matrix:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self._init_colors()
        self.resize()

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        if curses.can_change_color():
            curses.init_color(curses.COLOR_GREEN, 0, 1000, 0)
            curses.init_color(9, 300, 1000, 300)
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, 9, curses.COLOR_BLACK)
        else:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def resize(self):
        self.h, self.w = self.stdscr.getmaxyx()
        self.h = max(self.h, 1)
        self.w = max(self.w, 1)
        self.streams = [Stream(self.h) for _ in range(self.w)]

    def run(self):
        last = time.time()
        while True:
            now = time.time()
            dt = min(now - last, 0.1)
            last = now

            ch = self.stdscr.getch()
            if ch in (ord("q"), 27):
                break

            self.stdscr.erase()
            for x, stream in enumerate(self.streams):
                head_int = int(stream.head)
                for i in range(stream.trail):
                    y = head_int - i
                    if 0 <= y < self.h and x < self.w:
                        glyph = stream.glyphs[i % len(stream.glyphs)]
                        if i == 0:
                            attr = curses.color_pair(1) | curses.A_BOLD
                        elif i < 3:
                            attr = curses.color_pair(3) | curses.A_BOLD
                        else:
                            shade = max(0, 1 - i / stream.trail)
                            attr = curses.color_pair(2)
                            if shade < 0.4:
                                attr = curses.A_DIM
                        try:
                            self.stdscr.addstr(y, x, glyph, attr)
                        except curses.error:
                            pass
                stream.step(dt * 60)
                if stream.head - stream.trail > self.h:
                    stream.reset(self.h, top=True)

            self.stdscr.refresh()
            time.sleep(0.016)

def main(stdscr):
    Matrix(stdscr).run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
