#!/usr/bin/env python3
"""Animated Conway's Game of Life in the terminal (zero dependencies)."""
import argparse
import os
import random
import sys
import time


def _pulsar():
    # Standard 13 x 13 pulsar, centered so coordinates are symmetric.
    rows = [
        "..ooo...ooo..",
        "...........",
        "o....o.o....o",
        "o....o.o....o",
        "o....o.o....o",
        "..ooo...ooo..",
        "...........",
        "..ooo...ooo..",
        "o....o.o....o",
        "o....o.o....o",
        "o....o.o....o",
        "...........",
        "..ooo...ooo..",
    ]
    cells = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "o":
                cells.add((x - 6, y - 6))
    return cells


# Classic still lifes, oscillators, and spaceships.
PATTERNS = {
    "blinker": {(1, 0), (1, 1), (1, 2)},                        # oscillator, period 2
    "block": {(0, 0), (1, 0), (0, 1), (1, 1)},                  # still life
    "beehive": {(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)},
    "glider": {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)},         # spaceship
    "lwss": {                                                     # lightweight spaceship
        (1, 0), (4, 0),
        (0, 1),
        (0, 2), (4, 2),
        (0, 3), (1, 3), (2, 3), (3, 3),
    },
    "pulsar": _pulsar(),                                          # oscillator, period 3
}


def next_generation(cells):
    """Return the set of live cells after one Game of Life step."""
    neighbor_counts = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                key = (x + dx, y + dy)
                neighbor_counts[key] = neighbor_counts.get(key, 0) + 1

    offspring = set()
    for key, count in neighbor_counts.items():
        if count == 3 or (count == 2 and key in cells):
            offspring.add(key)
    return offspring


def render(cells, width, height, offset_x, offset_y):
    """Return a grid of characters for the current live cells."""
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append("#" if (x - offset_x, y - offset_y) in cells else ".")
        lines.append("".join(row))
    return "\n".join(lines)


def random_seed(width, height, density):
    cells = set()
    for y in range(height):
        for x in range(width):
            if random.random() < density:
                cells.add((x, y))
    return cells


def parse_args():
    parser = argparse.ArgumentParser(
        description="Animated Conway's Game of Life in the terminal."
    )
    parser.add_argument("pattern", nargs="?", default="glider",
                        help="pattern name or 'random' (default: glider)")
    parser.add_argument("-w", "--width", type=int, default=60)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("-f", "--fps", type=float, default=15)
    parser.add_argument("-g", "--generations", type=int, default=0,
                        help="stop after N generations (0 = run forever)")
    parser.add_argument("-d", "--density", type=float, default=0.35,
                        help="density for 'random' pattern (default: 0.35)")
    parser.add_argument("--wrap", action="store_true",
                        help="treat the grid as a torus so edges wrap")
    parser.add_argument("--list", action="store_true",
                        help="list available patterns and exit")
    return parser.parse_args()


def wrap_point(x, y, width, height):
    return (x % width, y % height)


def main():
    args = parse_args()

    if args.list:
        print("Patterns:")
        for name in sorted(PATTERNS):
            print(f"  {name}  ({len(PATTERNS[name])} cells)")
        print("  random  (randomly seeded)")
        return 0

    if args.width < 1 or args.height < 1:
        print("error: width and height must be positive", file=sys.stderr)
        return 2

    if args.pattern == "random":
        cells = random_seed(args.width, args.height, args.density)
    elif args.pattern in PATTERNS:
        cells = set(PATTERNS[args.pattern])
    else:
        print(f"error: unknown pattern '{args.pattern}'", file=sys.stderr)
        print("Run with --list to see available patterns.", file=sys.stderr)
        return 2

    # Center the pattern in the grid.
    if args.pattern != "random":
        xs = [x for x, _ in cells]
        ys = [y for _, y in cells]
        offset_x = args.width // 2 - (min(xs) + max(xs)) // 2
        offset_y = args.height // 2 - (min(ys) + max(ys)) // 2
    else:
        offset_x, offset_y = 0, 0

    generation = 0
    try:
        while args.generations == 0 or generation < args.generations:
            print(render(cells, args.width, args.height, offset_x, offset_y))
            print(f"generation {generation}  live cells {len(cells)}")
            time.sleep(1.0 / args.fps)
            if os.name == "nt":
                os.system("cls")
            else:
                sys.stdout.write("\033[H")   # move cursor home
                sys.stdout.flush()

            if args.wrap:
                cells = {wrap_point(x, y, args.width, args.height)
                         for x, y in next_generation(cells)}
            else:
                cells = next_generation(cells)
            generation += 1

            if not cells:
                print("All cells died out.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
