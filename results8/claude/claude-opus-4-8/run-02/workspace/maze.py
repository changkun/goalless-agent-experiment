#!/usr/bin/env python3
"""
maze.py — generate a maze and solve it, animated in the terminal.

Generation: recursive backtracker (depth-first carving) — produces long,
windy corridors with a satisfyingly "hand-drawn" feel.
Solving:    breadth-first search — guarantees the shortest path and floods
            outward so you can watch the frontier explore.

Usage:
    python3 maze.py [width] [height] [--seed N] [--fast]

Width/height are in cells (the drawn grid is roughly twice that).
"""

import sys
import time
import random
from collections import deque

# ─── tiny terminal helpers ──────────────────────────────────────────────────
ESC = "\033["
HIDE_CURSOR = ESC + "?25l"
SHOW_CURSOR = ESC + "?25h"
CLEAR = ESC + "2J" + ESC + "H"          # clear screen, cursor home
HOME = ESC + "H"

# 256-colour foreground
def fg(n: int) -> str:
    return f"{ESC}38;5;{n}m"

RESET = ESC + "0m"

WALL   = fg(240) + "█" + RESET          # dim grey wall
CARVE  = fg(35)  + "·" + RESET          # green, freshly carved
FRONT  = fg(45)  + "•" + RESET          # cyan, BFS frontier
PATH   = fg(220) + "◆" + RESET          # gold, final shortest path
SPACE  = " "

N, S, E, W = 1, 2, 4, 8
DX = {E: 1, W: -1, N: 0, S: 0}
DY = {E: 0, W: 0, N: -1, S: 1}
OPP = {E: W, W: E, N: S, S: N}


class Maze:
    def __init__(self, w, h, seed=None):
        self.w, self.h = w, h
        self.rng = random.Random(seed)
        self.cells = [[0] * w for _ in range(h)]   # bitmask of open walls

    # ── generation ──────────────────────────────────────────────────────────
    def carve(self, on_step=None):
        stack = [(0, 0)]
        seen = {(0, 0)}
        while stack:
            x, y = stack[-1]
            dirs = [N, S, E, W]
            self.rng.shuffle(dirs)
            for d in dirs:
                nx, ny = x + DX[d], y + DY[d]
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in seen:
                    self.cells[y][x] |= d
                    self.cells[ny][nx] |= OPP[d]
                    seen.add((nx, ny))
                    stack.append((nx, ny))
                    if on_step:
                        on_step(x, y)
                    break
            else:
                stack.pop()

    # ── solving (BFS, shortest path) ─────────────────────────────────────────
    def solve(self, on_visit=None):
        start, goal = (0, 0), (self.w - 1, self.h - 1)
        prev = {start: None}
        q = deque([start])
        while q:
            x, y = q.popleft()
            if on_visit:
                on_visit(x, y)
            if (x, y) == goal:
                break
            for d in (N, S, E, W):
                if self.cells[y][x] & d:
                    nx, ny = x + DX[d], y + DY[d]
                    if (nx, ny) not in prev:
                        prev[(nx, ny)] = (x, y)
                        q.append((nx, ny))
        # reconstruct
        path, node = [], goal
        while node is not None:
            path.append(node)
            node = prev.get(node)
        return path[::-1]

    # ── rendering ─────────────────────────────────────────────────────────────
    def render(self, overlay=None):
        """Return the maze as a grid of glyphs. overlay: {(x,y): glyph}."""
        overlay = overlay or {}
        H, W = self.h * 2 + 1, self.w * 2 + 1
        grid = [[WALL] * W for _ in range(H)]
        for y in range(self.h):
            for x in range(self.w):
                gx, gy = x * 2 + 1, y * 2 + 1
                grid[gy][gx] = overlay.get((x, y), SPACE)
                if self.cells[y][x] & E:
                    grid[gy][gx + 1] = overlay.get((x, y), SPACE)
                if self.cells[y][x] & S:
                    grid[gy + 1][gx] = overlay.get((x, y), SPACE)
        return grid


def draw(grid):
    sys.stdout.write(HOME)
    sys.stdout.write("\n".join("".join(row) for row in grid))
    sys.stdout.write("\n")
    sys.stdout.flush()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    seed = None
    if "--seed" in " ".join(sys.argv):
        # crude: look for "--seed N"
        for i, a in enumerate(sys.argv):
            if a == "--seed" and i + 1 < len(sys.argv):
                seed = int(sys.argv[i + 1])
                args = [x for x in args if x != str(seed)]

    w = int(args[0]) if len(args) > 0 else 28
    h = int(args[1]) if len(args) > 1 else 14
    pace = 0.0 if "--fast" in flags else None

    maze = Maze(w, h, seed=seed)
    sys.stdout.write(HIDE_CURSOR + CLEAR)
    try:
        # animate carving
        overlay = {}
        step = pace if pace is not None else max(0.004, 0.6 / (w * h))
        def on_carve(x, y):
            overlay[(x, y)] = CARVE
            draw(maze.render(overlay))
            time.sleep(step)
        maze.carve(on_carve)

        # animate BFS flood
        flood = {}
        def on_visit(x, y):
            flood[(x, y)] = FRONT
            draw(maze.render(flood))
            time.sleep(step)
        path = maze.solve(on_visit)

        # paint shortest path
        for (x, y) in path:
            flood[(x, y)] = PATH
            draw(maze.render(flood))
            time.sleep(step)

        draw(maze.render({**flood, **{p: PATH for p in path}}))
        print(f"\nSolved {w}×{h} maze — shortest path: {len(path)} cells"
              + (f"  (seed {seed})" if seed is not None else ""))
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
