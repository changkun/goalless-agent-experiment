#!/usr/bin/env python3
"""Conway's Game of Life — a zero-dependency terminal implementation.

Controls while the simulation is running:
    Space     pause / resume
    n         advance one generation while paused
    s         save current pattern
    l         load last saved pattern
    c         clear the board
    1..5      load preset (1: glider, 2: gosper glider gun, 3: pulsar,
              4: r-pentomino, 5: random soup)
    r         randomize
    q         quit
    ?         print help overlay
"""

import random
import sys
import time


PRESETS = {
    "1": ("glider", [
        (1, 0), (2, 1), (0, 2), (1, 2), (2, 2),
    ]),
    "2": ("gosper glider gun", [
        (1, 5), (1, 6), (2, 5), (2, 6), (11, 5), (11, 6), (11, 7), (12, 4),
        (12, 8), (13, 3), (13, 9), (14, 3), (14, 9), (15, 6), (16, 4),
        (16, 8), (17, 5), (17, 6), (17, 7), (18, 6), (21, 3), (21, 4),
        (21, 5), (22, 3), (22, 4), (22, 5), (23, 2), (23, 6), (25, 1),
        (25, 2), (25, 6), (25, 7), (35, 3), (35, 4), (36, 3), (36, 4),
    ]),
    "3": ("pulsar", [
        (x, y) for x, y in [
            (2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12),
            (4, 2), (5, 2), (6, 2), (4, 7), (5, 7), (6, 7),
            (4, 9), (5, 9), (6, 9), (4, 14), (5, 14), (6, 14),
            (7, 4), (7, 5), (7, 6), (7, 10), (7, 11), (7, 12),
            (9, 4), (9, 5), (9, 6), (9, 10), (9, 11), (9, 12),
            (10, 2), (11, 2), (12, 2), (10, 7), (11, 7), (12, 7),
            (10, 9), (11, 9), (12, 9), (10, 14), (11, 14), (12, 14),
            (14, 4), (14, 5), (14, 6), (14, 10), (14, 11), (14, 12),
        ]
    ]),
    "4": ("r-pentomino", [
        (1, 0), (2, 0), (0, 1), (1, 1), (1, 2),
    ]),
}


def center(cells, w, h):
    """Move a set of cells so their bounding box sits in the middle."""
    if not cells:
        return cells
    min_x = min(x for x, _ in cells)
    max_x = max(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    max_y = max(y for _, y in cells)
    dx = (w - (max_x - min_x)) // 2 - min_x
    dy = (h - (max_y - min_y)) // 2 - min_y
    return {(x + dx, y + dy) for x, y in cells}


def step(alive):
    """Advance one generation, returning the next set of live cells."""
    neighbor_counts = {}
    for x, y in alive:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                key = (x + dx, y + dy)
                neighbor_counts[key] = neighbor_counts.get(key, 0) + 1
    nxt = set()
    for cell, count in neighbor_counts.items():
        if count == 3 or (count == 2 and cell in alive):
            nxt.add(cell)
    return nxt


class Terminal:
    """Minimal raw-mode terminal wrapper using ANSI escapes."""

    def __init__(self):
        self.rows, self.cols = self._size()

    @staticmethod
    def _size():
        try:
            import shutil
            w, h = shutil.get_terminal_size((80, 24))
            return h, w
        except Exception:
            return 24, 80

    def clear(self):
        sys.stdout.write("\x1b[2J\x1b[H")

    def hide_cursor(self):
        sys.stdout.write("\x1b[?25l")

    def show_cursor(self):
        sys.stdout.write("\x1b[?25h")

    def home(self):
        sys.stdout.write("\x1b[H")

    @staticmethod
    def set_raw(enabled):
        try:
            import termios
            import tty
            if enabled:
                tty.setraw(sys.stdin.fileno())
            else:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))
        except Exception:
            pass


def read_key():
    """Non-blocking read of a single char from stdin, or None."""
    import select
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


def draw(term, alive, gen, paused, message=""):
    term.home()
    h, w = term.rows - 2, term.cols
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append("#" if (x, y) in alive else " ")
        out.append("".join(row))
    status = f"gen={gen} live={len(alive)}"
    if paused:
        status += " [PAUSED]"
    if message:
        status += f"  {message}"
    out.append(status.ljust(w - 1))
    out.append(f"space pause | n step | s save | l load | c clear | 1-4 presets | r random | ? help | q quit")
    sys.stdout.write("\n".join(out))
    sys.stdout.flush()


HELP = (
    "\x1b[2J\x1b[H"
    "CONWAY'S GAME OF LIFE\n"
    "\n"
    "  space      pause / resume\n"
    "  n          advance one generation (when paused)\n"
    "  s          save current pattern\n"
    "  l          load last saved pattern\n"
    "  c          clear the board\n"
    "  1          glider\n"
    "  2          gosper glider gun\n"
    "  3          pulsar\n"
    "  4          r-pentomino\n"
    "  5          random soup\n"
    "  r          randomize\n"
    "  ?          toggle this help\n"
    "  q          quit\n"
    "\n"
    "Press any key to continue..."
)


def main():
    term = Terminal()
    h, w = term.rows - 2, term.cols
    alive = PRESETS["2"][1]
    alive = center(alive, w, h)
    gen = 0
    paused = False
    showing_help = False
    saved = set()
    message = ""

    Terminal.set_raw(True)
    term.hide_cursor()
    term.clear()
    try:
        while True:
            if showing_help:
                sys.stdout.write(HELP)
                sys.stdout.flush()
                ch = sys.stdin.read(1)
                showing_help = False
                term.clear()
                continue

            # Advance the simulation.
            if not paused:
                alive = step(alive)
                gen += 1

            draw(term, alive, gen, paused, message)
            message = ""

            # Coarse timing loop; poll for keys in between ticks.
            tick = 0.06
            deadline = time.time() + tick
            while time.time() < deadline:
                key = read_key()
                if key is None:
                    time.sleep(0.01)
                    continue
                if key == " ":
                    paused = not paused
                elif key == "n":
                    if paused:
                        alive = step(alive)
                        gen += 1
                elif key == "s":
                    saved = set(alive)
                    message = "saved"
                elif key == "l":
                    if saved:
                        alive = set(saved)
                        message = "loaded"
                    else:
                        message = "nothing saved yet"
                elif key == "c":
                    alive = set()
                    message = "cleared"
                elif key in PRESETS:
                    alive = center(set(PRESETS[key][1]), w, h)
                    gen = 0
                    message = PRESETS[key][0]
                elif key == "5":
                    alive = random_soup(w, h)
                    gen = 0
                    message = "random soup"
                elif key == "r":
                    alive = random_soup(w, h)
                    gen = 0
                    message = "randomized"
                elif key == "?":
                    showing_help = True
                elif key in ("q", "\x1b"):  # q or ESC
                    return
                else:
                    continue
                # Redraw immediately after handling a key.
                draw(term, alive, gen, paused, message)
                message = ""
                time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        term.show_cursor()
        Terminal.set_raw(False)
        term.clear()
        sys.stdout.write("bye!\n")


def random_soup(w, h, density=0.18):
    return {
        (x, y)
        for x in range(w)
        for y in range(h)
        if random.random() < density
    }


if __name__ == "__main__":
    main()
