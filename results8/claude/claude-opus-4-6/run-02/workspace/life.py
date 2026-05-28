#!/usr/bin/env python3
import os, time, random

W, H = os.get_terminal_size().columns, os.get_terminal_size().lines - 1
grid = {(x, y) for x in range(W) for y in range(H) if random.random() < 0.2}

def step(g):
    candidates = set()
    for x, y in g:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidates.add((x + dx, y + dy))
    new = set()
    for cell in candidates:
        x, y = cell
        n = sum((x + dx, y + dy) in g for dx in (-1, 0, 1) for dy in (-1, 0, 1)) - (cell in g)
        if n == 3 or (n == 2 and cell in g):
            new.add(cell)
    return new

try:
    while True:
        buf = []
        for y in range(H):
            row = ""
            for x in range(W):
                row += "█" if (x, y) in grid else " "
            buf.append(row)
        print("\033[H" + "\n".join(buf), end="", flush=True)
        grid = step(grid)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\033[H\033[J", end="")
