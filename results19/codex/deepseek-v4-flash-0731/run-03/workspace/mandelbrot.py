#!/usr/bin/env python3
"""Interactive Mandelbrot set explorer for the terminal.

Controls:
    Arrow keys / WASD ... pan
    +/- q/a ............. zoom in / out
    c ................... toggle color palette
    h ................... cycle color hue
    r ................... reset view
    ? ................... show help
    q / ESC / Ctrl-C .... quit
"""

import os
import shutil
import sys

# ANSI 256-color palette for the escape-time gradient.
PALETTES = {
    "fire":   [16 + 6 * i + 6 for i in range(5)] + [124 + 4 * i for i in range(34)],
    "ocean":  [17 + i for i in range(28)] + [38 + i for i in range(22)],
    "forest": [22 + 2 * i for i in range(30)] + [70 + 3 * i for i in range(28)],
    "grape":  [53 + 5 * i for i in range(20)] + [90 + 3 * i for i in range(30)],
}

# Default view: x real axis, y imaginary axis (multiplied by -1 for screen).
X_MIN, X_MAX = -2.2, 0.9
Y_MIN, Y_MAX = -1.15, 1.15
MAX_ITER = 90


class Explorer:
    def __init__(self):
        self.x_min, self.x_max = X_MIN, X_MAX
        self.y_min, self.y_max = Y_MIN, Y_MAX
        self.max_iter = MAX_ITER
        self.palette_key = "fire"
        self.hue = 0
        self.paused = True  # first frame shown immediately
        self.msg = "Mandelbrot Explorer"
        self.msg_t = 0

    def reset(self):
        self.x_min, self.x_max = X_MIN, X_MAX
        self.y_min, self.y_max = Y_MIN, Y_MAX
        self.max_iter = MAX_ITER

    def note(self, text):
        self.msg = text
        self.msg_t = 0

    def iterate(self, cx, cy):
        """Return escape time for point (cx, cy)."""
        zx, zy = 0.0, 0.0
        for i in range(self.max_iter):
            zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
            if zx * zx + zy * zy > 4.0:
                return i
        return -1  # in the set


def render(ex, cols, rows):
    """Render the viewport to a list of (color, cell) tuples."""
    cells = []
    x_step = (ex.x_max - ex.x_min) / cols
    y_step = (ex.y_max - ex.y_min) / rows
    palette = build_palette(ex)
    for r in range(rows):
        cy = ex.y_max - y_step * r  # screen row 0 at top -> highest y
        cx = ex.x_min
        for _ in range(cols):
            it = ex.iterate(cx, cy)
            if it < 0:
                color, cell = 250, " "  # deep interior
            else:
                color = palette[it % len(palette)]
                cell = " .:-=+*#%@"[it % 10]
            cells.append((color, cell))
            cx += x_step
    return cells


def build_palette(ex):
    pal = list(PALETTES[ex.palette_key])
    if ex.hue:
        pal = pal[ex.hue:] + pal[:ex.hue]
    return pal


def draw(ex, cols, rows):
    out = []
    data = render(ex, cols, rows)
    for i in range(0, len(data), cols):
        row = data[i:i + cols]
        line = "".join(f"\x1b[38;5;{c}m{s}" for c, s in row)
        out.append(line)
    return "\n".join(out)


def screen_size():
    size = shutil.get_terminal_size((80, 24))
    return max(20, size.columns), max(10, size.lines - 3)


def move(ex, dx, dy, cols, rows):
    dw = ex.x_max - ex.x_min
    dh = ex.y_max - ex.y_min
    ex.x_min += dx * dw
    ex.x_max += dx * dw
    # Note: screen y is inverted; dy>0 moves the view center downward.
    ex.y_min += dy * dh
    ex.y_max += dy * dh


def zoom(ex, factor):
    cx = (ex.x_min + ex.x_max) / 2
    cy = (ex.y_min + ex.y_max) / 2
    w = (ex.x_max - ex.x_min) * factor
    h = (ex.y_max - ex.y_min) * factor
    ex.x_min, ex.x_max = cx - w / 2, cx + w / 2
    ex.y_min, ex.y_max = cy - h / 2, cy + h / 2
    if w < 1e-12:
        ex.note("Zoom limit reached")
        ex.reset()


def help_text():
    return (
        "\x1b[38;5;250m"
        "Controls: arrows/WASD pan | + / - zoom | c palette | h hue | r reset | ? help | q quit"
    )


def run():
    os.system("stty -echo -icanon min 1 time 0" if sys.stdin.isatty() else "")
    ex = Explorer()
    keys = {
        "\x1b[A": "up", "\x1b[B": "down", "\x1b[C": "right", "\x1b[D": "left",
        "w": "up", "s": "down", "a": "left", "d": "right",
        "+": "zin", "=": "zin", "-": "zout", "_": "zout",
        "c": "pal", "h": "hue", "r": "reset", "?": "help", "\x1b": "quit", "q": "quit",
    }
    show_help = True
    try:
        while True:
            cols, rows = screen_size()
            print("\x1b[2J\x1b[H", end="")
            print(draw(ex, cols, rows))
            status = (f"{ex.palette_key} | iter {ex.max_iter} | "
                      f"x[{ex.x_min:.4f},{ex.x_max:.4f}] "
                      f"y[{ex.y_min:.4f},{ex.y_max:.4f}]")
            print(f"\x1b[38;5;250m{status}", end="")
            if ex.msg_t < 5:
                print(f"   \x1b[38;5;214m{ex.msg}", end="")
            elif show_help:
                print("\n" + help_text(), end="")
            print("\x1b[0m")

            key = sys.stdin.read(1)
            if key == "\x1b":
                # Possibly an escape sequence; peek for the next two chars.
                seq = sys.stdin.read(2)
                name = keys.get("\x1b" + seq) or keys.get(seq) or keys.get(key)
            else:
                name = keys.get(key.lower())
            ex.msg_t += 1

            if name == "quit":
                break
            elif name == "up":
                move(ex, 0, 1, cols, rows)
            elif name == "down":
                move(ex, 0, -1, cols, rows)
            elif name == "left":
                move(ex, -1, 0, cols, rows)
            elif name == "right":
                move(ex, 1, 0, cols, rows)
            elif name == "zin":
                zoom(ex, 0.7)
                ex.max_iter = min(2000, ex.max_iter + 5)
            elif name == "zout":
                zoom(ex, 1.4)
                ex.max_iter = max(40, ex.max_iter - 5)
            elif name == "pal":
                order = list(PALETTES)
                ex.palette_key = order[(order.index(ex.palette_key) + 1) % len(order)]
                ex.note(f"palette = {ex.palette_key}")
            elif name == "hue":
                # Rebuild current palette shifted by hue (kept simple).
                ex.hue = (ex.hue + 1) % len(PALETTES[ex.palette_key])
                ex.note(f"hue shift {ex.hue}")
            elif name == "reset":
                ex.reset()
                ex.note("reset")
            elif name == "help":
                show_help = not show_help
    finally:
        os.system("stty echo icanon" if sys.stdin.isatty() else "")


if __name__ == "__main__":
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\x1b[0m")
