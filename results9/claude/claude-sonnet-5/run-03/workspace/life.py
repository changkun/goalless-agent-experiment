#!/usr/bin/env python3
"""Conway's Game of Life in the terminal.

Controls:
  space  pause / resume
  r      randomize
  c      clear
  click  toggle a cell (while paused)
  +/-    speed up / slow down
  q      quit
"""
import curses
import random

ALIVE, DEAD = "#", " "


class Board:
    def __init__(self, h, w):
        self.h, self.w = h, w
        self.cells = [[0] * w for _ in range(h)]

    def randomize(self, density=0.25):
        self.cells = [
            [1 if random.random() < density else 0 for _ in range(self.w)]
            for _ in range(self.h)
        ]

    def clear(self):
        self.cells = [[0] * self.w for _ in range(self.h)]

    def toggle(self, y, x):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.cells[y][x] ^= 1

    def step(self):
        h, w, cells = self.h, self.w, self.cells
        new = [[0] * w for _ in range(h)]
        for y in range(h):
            row_up, row, row_dn = cells[(y - 1) % h], cells[y], cells[(y + 1) % h]
            for x in range(w):
                xl, xr = (x - 1) % w, (x + 1) % w
                n = (
                    row_up[xl] + row_up[x] + row_up[xr]
                    + row[xl] + row[xr]
                    + row_dn[xl] + row_dn[x] + row_dn[xr]
                )
                new[y][x] = 1 if (n == 3 or (row[x] and n == 2)) else 0
        self.cells = new


def main(stdscr):
    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.nodelay(True)
    stdscr.timeout(120)

    max_y, max_x = stdscr.getmaxyx()
    h, w = max_y - 1, max_x
    board = Board(h, w)
    board.randomize()

    paused = False
    delay = 120
    generation = 0

    while True:
        stdscr.erase()
        for y in range(board.h):
            line = "".join(ALIVE if c else DEAD for c in board.cells[y])
            try:
                stdscr.addstr(y, 0, line)
            except curses.error:
                pass
        status = f" gen {generation} | {'PAUSED' if paused else 'running'} | space=pause r=random c=clear +/-=speed q=quit "
        try:
            stdscr.addstr(max_y - 1, 0, status[:max_x - 1], curses.A_REVERSE)
        except curses.error:
            pass
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == ord("q"):
            break
        elif ch == ord(" "):
            paused = not paused
        elif ch == ord("r"):
            board.randomize()
            generation = 0
        elif ch == ord("c"):
            board.clear()
            generation = 0
        elif ch in (ord("+"), ord("=")):
            delay = max(20, delay - 20)
            stdscr.timeout(delay)
        elif ch == ord("-"):
            delay = min(1000, delay + 20)
            stdscr.timeout(delay)
        elif ch == curses.KEY_MOUSE:
            _, mx, my, _, _ = curses.getmouse()
            board.toggle(my, mx)

        if not paused:
            board.step()
            generation += 1


if __name__ == "__main__":
    curses.wrapper(main)
