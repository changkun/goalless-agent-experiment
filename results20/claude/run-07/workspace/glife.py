#!/usr/bin/env python3
"""
glife.py — Conway's Game of Life in your terminal.

Zero dependencies. Run it and watch life evolve in glowing color.

Controls (while running):
  Space      pause / resume
  c          clear the board
  g          stamp a random glider gun pattern at the cursor
  p          stamp a pulsar at the cursor
  +/-        speed up / slow down
  s          single-step (while paused)
  q          quit

Drag with arrow keys to move the cursor; press a pattern key to stamp it.
"""
import argparse
import os
import random
import shutil
import sys
import time

# ---- Cell / palette ----
DEAD = 0
ALIVE = 1

# Glow palette: age (0..AGE_MAX) -> ANSI 24-bit color for a live cell.
# Young cells are bright, old cells cool toward violet.
AGE_MAX = 14
PALETTE = []
for a in range(AGE_MAX + 1):
    t = a / AGE_MAX
    r = int(70 + 185 * (1 - t))
    g = int(200 - 60 * t)
    b = int(150 + 105 * t)
    PALETTE.append(f"\x1b[38;2;{r};{g};{b}m")

RESET = "\x1b[0m"
GREEN = "\x1b[38;2;60;90;80m"  # faint grid for dead-but-neighbor cells
GREY = "\x1b[2m"

# ---- Patterns (as sets of (row, col) cells) ----
def _glider_gun():
    # Gosper glider gun, canonical coords.
    cells = {
        (5,1),(5,2),(6,1),(6,2),
        (3,13),(3,14),(4,12),(4,16),(5,11),(5,17),(6,11),(6,15),(6,17),(6,18),
        (7,11),(7,17),(7,18),(8,12),(8,16),(9,13),(9,14),
        (1,25),(2,23),(2,25),(3,21),(3,22),(4,21),(4,22),
        (1,35),(2,35),(3,35),
        (5,36),(6,37),(6,38),(7,37),
    }
    return cells

def _pulsar():
    cells = set()
    for a in range(3):
        for b in range(3):
            cells.add((a, b)); cells.add((a + 2, b + 2))
    # build one quadrant then mirror
    proto = {(r, c) for (r, c) in [
        (0,2),(0,3),(0,4),(2,0),(3,0),(4,0),
        (2,6),(3,6),(4,6),(6,2),(6,3),(6,4),
    ]}
    out = set()
    for r, c in proto:
        for sr in (r, 9 - r):
            for sc in (c, 9 - c):
                out.add((sr, sc))
    return out

PATTERNS = {
    "gun":   (_glider_gun, "Gosper glider gun"),
    "pulsar": (_pulsar, "Pulsar"),
}

def make_board(cols, rows, density=0.18):
    board = [[0] * cols for _ in range(rows)]
    age = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if random.random() < density:
                board[r][c] = ALIVE
    return board, age

def count_neighbors(board, cols, rows, r, c):
    n = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr = (r + dr) % rows
            cc = (c + dc) % cols
            n += board[rr][cc]
    return n

def step(board, age, cols, rows):
    new = [[0] * cols for _ in range(rows)]
    newage = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        row = board[r]
        for c in range(cols):
            n = count_neighbors(board, cols, rows, r, c)
            if row[c]:
                new[r][c] = ALIVE if n in (2, 3) else DEAD
                newage[r][c] = 0 if new[r][c] == DEAD else min(age[r][c] + 1, AGE_MAX)
            elif n == 3:
                new[r][c] = ALIVE
    return new, newage

def stamp(board, cells, origin, cols, rows, clear_first=False):
    r0, c0 = origin
    if clear_first:
        for r in range(rows):
            for c in range(cols):
                board[r][c] = DEAD
    minr = min(r for r, _ in cells); minc = min(c for _, c in cells)
    for r, c in cells:
        rr = r0 + (r - minr)
        cc = c0 + (c - minc)
        if 0 <= rr < rows and 0 <= cc < cols:
            board[rr][cc] = ALIVE

def render(board, age, cols, rows, cursor, generation, paused, speed):
    out = ["\x1b[H\x1b[2J"]
    cr, cc = cursor
    for r in range(rows):
        line = []
        for c in range(cols):
            if board[r][c]:
                line.append(PALETTE[min(age[r][c], AGE_MAX)] + "█")
            else:
                # faint dot for cells about to be born from neighbors
                n = count_neighbors(board, cols, rows, r, c)
                if n == 3:
                    line.append(GREEN + "·")
                else:
                    line.append(GREY + " ")
            line.append(RESET)
        out.append("".join(line))
    # status line
    status = (f"gen {generation}   birth rate {int(sum(sum(b) for b in board))}   "
              f"{'PAUSED' if paused else 'RUNNING'}   "
              f"speed {speed:>2}   <space> pause  <c> clear  <g>/<p> stamp  <q> quit")
    out.append(status + RESET)
    sys.stdout.write("\n".join(out))
    sys.stdout.flush()

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cols", type=int, default=0)
    ap.add_argument("--rows", type=int, default=0)
    ap.add_argument("--density", type=float, default=0.18)
    args = ap.parse_args()

    term = shutil.get_terminal_size((80, 24))
    cols = args.cols or max(20, term.columns - 2)
    rows = args.rows or max(10, term.lines - 3)

    board, age = make_board(cols, rows, args.density)
    cursor = [rows // 2, cols // 2]
    generation = 0
    paused = False
    speed = 10  # generations per second (nominal)
    global PALETTE

    # Raw terminal mode
    old = None
    if sys.stdin.isatty():
        import termios, tty
        old = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    sys.stdout.write("\x1b[?25l")  # hide cursor
    import select
    try:
        last = time.time()
        try:
            while True:
                render(board, age, cols, rows, cursor, generation, paused, speed)

                now = time.time()
                # If not paused, block briefly until the next step is due
                # (giving the render loop a natural cadence); otherwise poll
                # fast so arrows/space respond snappily while paused.
                wait = 1.0 / speed if not paused else 0.03
                ready, _, _ = select.select([sys.stdin], [], [], wait)
                if ready:
                    ch = sys.stdin.read(1)
                    if ch == "":  # EOF (e.g. redirected stdin)
                        break
                    elif ch == "q":
                        break
                    elif ch == " ":
                        paused = not paused
                    elif ch == "c":
                        for r in range(rows):
                            for c in range(cols):
                                board[r][c] = DEAD
                    elif ch == "g":
                        stamp(board, PATTERNS["gun"][0](), cursor, cols, rows)
                    elif ch == "p":
                        stamp(board, PATTERNS["pulsar"][0](), cursor, cols, rows)
                    elif ch == "+":
                        speed = min(120, speed + 10)
                    elif ch == "-":
                        speed = max(1, speed - 10)
                    elif ch == "s":
                        paused = True
                        board, age = step(board, age, cols, rows)
                        generation += 1
                    elif ch in "\x1b":
                        # arrow keys: ESC [ A/B/C/D
                        seq = sys.stdin.read(2)
                        if seq == "[A":
                            cursor[0] = (cursor[0] - 1) % rows
                        elif seq == "[B":
                            cursor[0] = (cursor[0] + 1) % rows
                        elif seq == "[C":
                            cursor[1] = (cursor[1] + 1) % cols
                        elif seq == "[D":
                            cursor[1] = (cursor[1] - 1) % cols

                if not paused and (time.time() - last) >= 1.0 / speed:
                    board, age = step(board, age, cols, rows)
                    generation += 1
                    last = time.time()

        except KeyboardInterrupt:
            pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m")
        if old is not None:
            import termios, tty
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
        print()

if __name__ == "__main__":
    main()
