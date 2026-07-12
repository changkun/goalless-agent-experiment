#!/usr/bin/env python3
"""
Conway's Game of Life — a tiny terminal edition.

Run:  python3 life.py
Controls:
  q / Ctrl-C  → quit
  +/-         → speed up / slow down
  r           → randomize the board
  Space       → pause / resume
"""

import os
import sys
import time
import random
import select
import termios
import tty

# ── board ────────────────────────────────────────────────────────────
def make_board(rows, cols, density=0.3):
    return [[random.random() < density for _ in range(cols)] for _ in range(rows)]

def neighbours(board, r, c, rows, cols):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % rows, (c + dc) % cols
            count += board[nr][nc]
    return count

def step(board, rows, cols):
    new = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = neighbours(board, r, c, rows, cols)
            if board[r][c]:
                new[r][c] = n in (2, 3)
            else:
                new[r][c] = n == 3
    return new

# ── rendering ────────────────────────────────────────────────────────
ALIVE = "█"
DEAD  = " "

def render(board, gen, delay, paused):
    size = os.get_terminal_size()
    buf = [f"\033[H\033[J\033[1;36m Game of Life \033[0m │ gen {gen}  │ delay {delay:.2f}s  │ {'⏸  PAUSED' if paused else '▶  running'}\n"]
    for row in board:
        buf.append("".join(ALIVE if c else DEAD for c in row))
        buf.append("\n")
    buf.append("\033[2m q quit · +/- speed · r randomize · space pause\033[0m")
    sys.stdout.write("".join(buf))
    sys.stdout.flush()

# ── input ────────────────────────────────────────────────────────────
def get_key(timeout):
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        return sys.stdin.read(1)
    return None

# ── main loop ────────────────────────────────────────────────────────
def main():
    size = os.get_terminal_size()
    rows = size.lines - 3
    cols = size.columns
    if rows < 5 or cols < 10:
        print("Terminal too small!")
        return

    board = make_board(rows, cols)
    gen = 0
    delay = 0.10
    paused = False

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            render(board, gen, delay, paused)
            key = get_key(0 if paused else delay)
            if key == "q":
                break
            elif key == "+":
                delay = max(0.02, delay - 0.02)
            elif key == "-":
                delay = min(1.0, delay + 0.02)
            elif key == "r":
                board = make_board(rows, cols)
                gen = 0
            elif key == " ":
                paused = not paused
            if not paused:
                board = step(board, rows, cols)
                gen += 1
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()
        print("Thanks for watching life unfold! 🧬")

if __name__ == "__main__":
    main()
