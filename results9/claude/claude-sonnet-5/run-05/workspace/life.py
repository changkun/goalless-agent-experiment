#!/usr/bin/env python3
"""Conway's Game of Life, rendered live in the terminal."""
import sys
import time

WIDTH, HEIGHT = 50, 25

GOSPER_GLIDER_GUN = """
........................O...........
......................O.O...........
............OO......OO............OO
...........O...O....OO............OO
OO........O.....O...OO..............
OO........O...O.OO....O.O...........
..........O.....O.......O...........
...........O...O.....................
............OO.......................
"""

def load_pattern(text, ox=1, oy=1):
    cells = set()
    for y, row in enumerate(text.strip("\n").split("\n")):
        for x, ch in enumerate(row):
            if ch == "O":
                cells.add((x + ox, y + oy))
    return cells

def step(cells):
    counts = {}
    for (x, y) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                counts[(x + dx, y + dy)] = counts.get((x + dx, y + dy), 0) + 1
    new_cells = set()
    for pos, n in counts.items():
        if n == 3 or (n == 2 and pos in cells):
            new_cells.add(pos)
    return new_cells

def render(cells, gen):
    lines = [f"Generation {gen} — Gosper Glider Gun  ('q'+Enter to stop)"]
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            row.append("█" if (x, y) in cells else " ")
        lines.append("".join(row))
    return "\n".join(lines)

def main():
    cells = load_pattern(GOSPER_GLIDER_GUN, ox=2, oy=2)
    gen = 0
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    try:
        for _ in range(frames):
            sys.stdout.write("\x1b[H\x1b[J")
            sys.stdout.write(render(cells, gen))
            sys.stdout.flush()
            cells = step(cells)
            gen += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    print()

if __name__ == "__main__":
    main()
