#!/usr/bin/env python3
"""Conway's Game of Life in the terminal, with color-aged cells.

Usage:
    python3 life.py [pattern] [generations]

Patterns: soup (default), glider, gosper, pulsar, rpentomino
Cells change color as they age: newborns are bright green, elders fade to blue.
"""
import random
import sys
import time

WIDTH, HEIGHT = 72, 30

PATTERNS = {
    "glider": ["(1,0)", "(2,1)", "(0,2)", "(1,2)", "(2,2)"],
    "rpentomino": ["(1,0)", "(2,0)", "(0,1)", "(1,1)", "(1,2)"],
    "pulsar": [],  # built programmatically below
    "gosper": [
        "(24,0)", "(22,1)", "(24,1)", "(12,2)", "(13,2)", "(20,2)", "(21,2)",
        "(34,2)", "(35,2)", "(11,3)", "(15,3)", "(20,3)", "(21,3)", "(34,3)",
        "(35,3)", "(0,4)", "(1,4)", "(10,4)", "(16,4)", "(20,4)", "(21,4)",
        "(0,5)", "(1,5)", "(10,5)", "(14,5)", "(16,5)", "(17,5)", "(22,5)",
        "(24,5)", "(10,6)", "(16,6)", "(24,6)", "(11,7)", "(15,7)", "(12,8)",
        "(13,8)",
    ],
}


def build_pulsar():
    cells = set()
    for dx in (2, 3, 4, 8, 9, 10):
        for dy in (0, 5, 7, 12):
            cells.add((dx, dy))
            cells.add((dy, dx))
    return cells


def parse(coords):
    return {tuple(int(n) for n in c.strip("()").split(",")) for c in coords}


def initial_board(name):
    ages = {}
    if name == "soup":
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if random.random() < 0.28:
                    ages[(x, y)] = 1
        return ages
    cells = build_pulsar() if name == "pulsar" else parse(PATTERNS[name])
    max_x = max(x for x, _ in cells)
    max_y = max(y for _, y in cells)
    off_x = (WIDTH - max_x) // 2 if name != "gosper" else 2
    off_y = (HEIGHT - max_y) // 2 if name != "gosper" else 2
    for x, y in cells:
        ages[(x + off_x, y + off_y)] = 1
    return ages


def neighbors(x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                yield (x + dx) % WIDTH, (y + dy) % HEIGHT


def step(ages):
    counts = {}
    for cell in ages:
        for n in neighbors(*cell):
            counts[n] = counts.get(n, 0) + 1
    nxt = {}
    for cell, count in counts.items():
        if count == 3 or (count == 2 and cell in ages):
            nxt[cell] = ages.get(cell, 0) + 1
    return nxt


def color_for(age):
    palette = [46, 82, 118, 154, 190, 220, 208, 39, 27]
    return palette[min(age - 1, len(palette) - 1)]


def render(ages, gen, name):
    rows = [f"\x1b[H\x1b[2K Game of Life  pattern={name}  gen={gen}  pop={len(ages)}"]
    for y in range(HEIGHT):
        line = []
        for x in range(WIDTH):
            age = ages.get((x, y))
            if age:
                line.append(f"\x1b[38;5;{color_for(age)}m██\x1b[0m")
            else:
                line.append("\x1b[38;5;236m··\x1b[0m")
        rows.append("".join(line))
    sys.stdout.write("\n".join(rows) + "\n")
    sys.stdout.flush()


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "soup"
    gens = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    if name != "soup" and name not in PATTERNS:
        sys.exit(f"unknown pattern {name!r}; try: soup, {', '.join(PATTERNS)}")
    ages = initial_board(name)
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        for gen in range(gens):
            render(ages, gen, name)
            ages = step(ages)
            if not ages:
                render(ages, gen + 1, name)
                print(" everyone died. so it goes.")
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\n")


if __name__ == "__main__":
    main()
