#!/usr/bin/env python3
"""nightscape — generate a one-of-a-kind ASCII mountain night scene.

Usage: python3 nightscape.py [seed]
Same seed, same landscape. No seed, a new one every run.
"""

import random
import sys

WIDTH, HEIGHT = 78, 24


def ridge(width, roughness, lo, hi, rng):
    """Midpoint-displacement heightline across `width` columns."""
    size = 1
    while size + 1 < width:
        size *= 2
    pts = [None] * (size + 1)
    pts[0] = rng.uniform(lo, hi)
    pts[size] = rng.uniform(lo, hi)
    step, disp = size, (hi - lo) / 2
    while step > 1:
        half = step // 2
        for i in range(half, size, step):
            mid = (pts[i - half] + pts[i + half]) / 2
            pts[i] = mid + rng.uniform(-disp, disp)
        step = half
        disp *= roughness
    return [min(hi, max(lo, p)) for p in pts[:width]]


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10**6)
    rng = random.Random(seed)
    canvas = [[" "] * WIDTH for _ in range(HEIGHT)]

    # stars
    for _ in range(rng.randint(28, 45)):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT * 2 // 3)
        canvas[y][x] = rng.choice("..**+'.")

    # moon
    mx, my = rng.randint(6, WIDTH - 10), rng.randint(1, 4)
    moon = ["  ___  ", " /   \\ ", "(     )", " \\___/ "]
    for dy, row in enumerate(moon):
        for dx, ch in enumerate(row):
            if ch != " " and 0 <= my + dy < HEIGHT and 0 <= mx + dx < WIDTH:
                canvas[my + dy][mx + dx] = ch

    # mountain layers, back to front
    layers = [
        (0.55, HEIGHT * 0.35, HEIGHT * 0.60, "-"),
        (0.62, HEIGHT * 0.50, HEIGHT * 0.75, "="),
        (0.70, HEIGHT * 0.65, HEIGHT * 0.92, "#"),
    ]
    for rough, lo, hi, fill in layers:
        line = ridge(WIDTH, rough, lo, hi, rng)
        for x, h in enumerate(line):
            top = int(h)
            for y in range(top, HEIGHT):
                canvas[y][x] = fill
            if 0 <= top - 1 < HEIGHT:
                canvas[top - 1][x] = "^" if fill == "#" else "~"

    # a lone cabin with a lit window on the front ridge
    cx = rng.randint(8, WIDTH - 12)
    ground = next((y for y in range(HEIGHT) if canvas[y][cx] == "#"), HEIGHT - 3)
    cabin = [" /\\ ", "/__\\", "|[]|"]
    for dy, row in enumerate(cabin):
        for dx, ch in enumerate(row):
            y, x = ground - len(cabin) + dy, cx + dx
            if ch != " " and 0 <= y < HEIGHT and 0 <= x < WIDTH:
                canvas[y][x] = ch

    print("+" + "-" * WIDTH + "+")
    for row in canvas:
        print("|" + "".join(row) + "|")
    print("+" + "-" * WIDTH + "+")
    print(f"  nightscape #{seed} — rerun with: python3 nightscape.py {seed}")


if __name__ == "__main__":
    main()
