#!/usr/bin/env python3
"""
Conway's Game of Life — a polished, self-contained terminal version.

Features:
  * Live ASCII grid with heat-based coloring (fresh cells brighter).
  * Toroidal (wrap-around) universe.
  * Several classic initial patterns.
  * HUD showing generation, live population, and toggled stats.
  * Keyboard controls: pause/resume, step, speed, clear, random, save/load,
    and a "virus" that injects random live cells while paused.
  * Zero dependencies — pure stdlib.

Controls:
  space   pause / resume
  n       advance one generation (while paused)
  c       clear the board
  r       random board (density ~30%)
  v       inject a random virus (adds live cells while running)
  s / l   save / load the current board to/from a file
  [ / ]   slower / faster
  q       quit
  h       toggle HUD
  ?       this help
"""

import argparse
import random
import sys
import time

try:
    import termios
    import tty
    _TTY_AVAILABLE = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _TTY_AVAILABLE = False


# --------------------------------------------------------------------------- #
# Patterns (each a list of (row, col) offsets, normalized to origin)
# --------------------------------------------------------------------------- #
def _norm(shape):
    rows = [r for r, _ in shape]
    cols = [c for _, c in shape]
    return [(r - min(rows), c - min(cols)) for r, c in shape]


PATTERNS = {
    "glider": _norm([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]),
    "blinker": _norm([(0, 1), (1, 1), (2, 1)]),
    "toad": _norm([(1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)]),
    "beacon": _norm([(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)]),
    "pulsar": _norm(
        [(2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12),
         (4, 2), (4, 7), (4, 9), (4, 14),
         (5, 2), (5, 7), (5, 9), (5, 14),
         (6, 2), (6, 7), (6, 9), (6, 14),
         (7, 4), (7, 5), (7, 6), (7, 10), (7, 11), (7, 12),
         (9, 4), (9, 5), (9, 6), (9, 10), (9, 11), (9, 12),
         (10, 2), (10, 7), (10, 9), (10, 14),
         (11, 2), (11, 7), (11, 9), (11, 14),
         (12, 2), (12, 7), (12, 9), (12, 14),
         (14, 4), (14, 5), (14, 6), (14, 10), (14, 11), (14, 12),]
    ),
    "gosper": _norm(
        # Gosper glider gun — placed in a 36x9 region centered near origin.
        [(5, 1), (5, 2),           # left block
         (6, 1), (6, 2),
         (3, 13), (3, 14), (4, 12), (4, 16), (5, 11), (5, 17),
         (6, 11), (6, 15), (6, 17), (6, 18), (7, 11), (7, 17),
         (8, 12), (8, 16), (9, 13), (9, 14),
         (1, 25), (2, 23), (2, 25),            # right gun
         (3, 21), (3, 22),
         (4, 21), (4, 22),
         (5, 21), (5, 22),
         (6, 23), (6, 25),
         (7, 25),                              # detonator
         (3, 35), (3, 36),
         (4, 35), (4, 36),]
    ),
}

PATTERN_NAMES = list(PATTERNS)


def place(world, pattern, r0, c0):
    for dr, dc in pattern:
        r, c = world._wrap(r0 + dr, c0 + dc)
        world.grid[r][c] = 1


# --------------------------------------------------------------------------- #
# Board — a simple 2D int array (list of lists) with alive-age tracking
# --------------------------------------------------------------------------- #
class Board:
    """Holds cells as 0 (dead) or 1..N (alive; value = consecutive time alive)."""

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.grid = [[0] * width for _ in range(height)]

    # -- basic geometry helpers ------------------------------------------- #
    def _wrap(self, r, c):
        return r % self.height, c % self.width

    def neighbors(self, r, c):
        """Count live neighbors (treat any nonzero as alive)."""
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = self._wrap(r + dr, c + dc)
                count += 1 if self.grid[nr][nc] else 0
        return count

    def step(self):
        """Advance one generation in place; return (born, survived, died)."""
        born = survived = died = 0
        new = [[0] * self.width for _ in range(self.height)]
        for r in range(self.height):
            for c in range(self.width):
                n = self.neighbors(r, c)
                alive = bool(self.grid[r][c])
                if alive:
                    if n in (2, 3):
                        new[r][c] = self.grid[r][c] + 1
                        survived += 1
                    else:
                        died += 1
                else:
                    if n == 3:
                        new[r][c] = 1
                        born += 1
        self.grid = new
        return born, survived, died

    def population(self):
        return sum(1 for row in self.grid for cell in row if cell)

    def clear(self):
        self.grid = [[0] * self.width for _ in range(self.height)]

    def randomize(self, density=0.3, seed=None):
        rng = random.Random(seed)
        self.grid = [
            [1 if rng.random() < density else 0 for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def virus(self, amount):
        """Randomly revive `amount` cells (with random birth timestamps)."""
        rng = random.Random()
        for _ in range(amount):
            r, c = rng.randrange(self.height), rng.randrange(self.width)
            self.grid[r][c] = rng.randint(1, 4)

    def save(self, path):
        with open(path, "w") as f:
            for row in self.grid:
                f.write("".join("#" if c else "." for c in row) + "\n")

    def load(self, path):
        rows = []
        with open(path) as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                rows.append([1 if ch in "#@" else 0 for ch in line])
        if not rows:
            raise ValueError("empty file")
        h, w = len(rows), len(rows[0])
        self.grid = [[0] * self.width for _ in range(self.height)]
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                if val and i < self.height and j < self.width:
                    self.grid[i][j] = val


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
# ANSI foreground colors. Cell brightness rises with age: young = dim,
# mature = bright. We pick from a small ramp per terminal.
RAMP = {
    1: 90,    # dark gray
    2: 33,    # bright blue-ish
    3: 36,    # cyan
    4: 33,    # yellow (via bold later)
    5: 93,    # bright yellow
}
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
CLEAR = "\x1b[2J\x1b[H"


def render(board, max_age=5):
    """Render the board to a list of ANSI-colored strings (one per row)."""
    age_max = max_age if 1 <= max_age <= len(RAMP) else len(RAMP)
    out = []
    for row in board.grid:
        cells = []
        for cell in row:
            if cell:
                age = cell if cell <= age_max else age_max
                color = RAMP[age]
                cells.append(f"\x1b[{color}mOO{RESET}")
            else:
                cells.append("  ")
        out.append("".join(cells))
    return out


# --------------------------------------------------------------------------- #
# Terminal handling
# --------------------------------------------------------------------------- #
class RawInput:
    """Non-blocking single-key reader on POSIX (raw mode), else line-based."""

    def __init__(self):
        self.raw = _TTY_AVAILABLE and sys.stdin.isatty()

    def __enter__(self):
        if self.raw:
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def poll(self, timeout=0.0):
        """Return a key if pressed within `timeout` seconds, else None."""
        import select
        r, _, _ = select.select([sys.stdin], [], [], timeout)
        if not r:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":  # escape sequences (arrows etc.) — swallow
            seq = sys.stdin.read(2)
            return f"\x1b{seq}"
        return ch

    def __exit__(self, *exc):
        if self.raw:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def run(board, args, fps):
    paused = False
    gen = 0
    stats = {"born": 0, "survived": 0, "died": 0}
    show_help = False

    def write_hud(rows, width):
        pad = max(0, width - 4)
        live = board.population()
        stat_line = (
            f" {BOLD}gen {gen}{RESET}  {live} alive "
            f"  {fps:.0f} fps  "
            f"[{BOLD}{'paused' if paused else 'running'}{RESET}]  "
        )
        hud = " " * pad + stat_line.rstrip()
        rows.append("")
        rows.append(hud)
        rows.append(" " * pad + " s=save l=load r=rand v=virus c=clear n=step [ ]=speed q=quit")

    def render_frame():
        rows = render(board)
        if show_help:
            rows = help_lines
        if not show_help and args.hud:
            write_hud(rows, board.width * 2)
        return CLEAR + "\n".join(rows)

    help_lines = [
        BOLD + " Conway's Game of Life " + RESET,
        "",
        "  space  pause / resume",
        "  n      advance one generation (while paused)",
        "  c      clear the board",
        "  r      random board",
        "  v      inject random live cells (a 'virus')",
        "  s / l  save / load board to/from a file",
        "  [ / ]  slower / faster",
        "  h      toggle HUD",
        "  ?      this help",
        "  q      quit",
    ]

    print(CLEAR, end="")
    with RawInput() as kb:
        while True:
            print(render_frame(), end="", flush=True)
            delay = 1.0 / fps if not paused else 0.05
            key = kb.poll(delay)

            if key is not None:
                if key in ("q", "Q"):
                    break
                elif key == " ":
                    paused = not paused
                elif key == "n":
                    b, s, d = board.step()
                    gen += 1
                    for lbl, val in (("born", b), ("survived", s), ("died", d)):
                        stats[lbl] += val
                elif key == "c":
                    board.clear()
                elif key == "r":
                    board.randomize(density=args.density)
                elif key == "v":
                    board.virus(args.virus_amount)
                elif key == "s":
                    board.save(args.file_out or "life_board.txt")
                elif key == "l":
                    try:
                        board.load(args.load or "life_board.txt")
                    except (OSError, ValueError) as e:
                        print(f"\r\x1b[31mload failed: {e}{RESET}")
                elif key == "[":
                    fps = max(1.0, fps / 1.5)
                elif key == "]":
                    fps = min(120.0, fps * 1.5)
                elif key == "h":
                    args.hud = not args.hud
                elif key == "?":
                    show_help = not show_help

            if not paused:
                board.step()
                gen += 1

    print(CLEAR, end="")
    print(f"Ended at generation {gen} with {board.population()} alive cells.")
    print(f"Lifetime stats: born={stats['born']} survived={stats['survived']} died={stats['died']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Conway's Game of Life in your terminal")
    ap.add_argument("--pattern", choices=PATTERN_NAMES, default="glider",
                    help="initial pattern (default: glider)")
    ap.add_argument("--rows", type=int, default=22, help="grid height")
    ap.add_argument("--cols", type=int, default=38, help="grid width (each cell = 2 chars)")
    ap.add_argument("--fps", type=float, default=8.0, help="generations per second")
    ap.add_argument("--density", type=float, default=0.30,
                    help="density for --random / random boards")
    ap.add_argument("--random", action="store_true", help="start with a random board")
    ap.add_argument("--virus-amount", type=int, default=15,
                    help="cells revived per virus injection")
    ap.add_argument("--no-hud", dest="hud", action="store_false", default=True,
                    help="hide the status line")
    ap.add_argument("--file-out", help="path used by the 's' save key")
    ap.add_argument("--load", help="path loaded by the 'l' key")
    args = ap.parse_args(argv)

    board = Board(args.rows, args.cols)
    if args.random:
        board.randomize(density=args.density)
    else:
        pat = PATTERNS[args.pattern]
        place(board, pat, args.rows // 2 - 2, args.cols // 2 - max(c for _, c in pat) // 2)

    run(board, args, args.fps)


if __name__ == "__main__":
    main()
