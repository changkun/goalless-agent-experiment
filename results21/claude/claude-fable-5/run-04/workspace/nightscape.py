#!/usr/bin/env python3
"""nightscape.py — generate a random ASCII night landscape.

Usage:
    python3 nightscape.py [seed]

Each seed produces a different scene: layered mountain ridges under a
starry sky, a moon in a random phase and position, and water below
with a shimmering reflection of the moonlight.
"""

import math
import random
import sys

WIDTH = 78
SKY_H = 14      # rows of sky (stars + moon + ridge tops)
LAND_H = 6      # rows where ridges resolve to ground
WATER_H = 5     # rows of water


def ridge_heights(rng, width, base, amplitude, roughness):
    """Midpoint-displacement heightline: smooth but craggy."""
    n = 1
    while n < width:
        n *= 2
    heights = [0.0] * (n + 1)
    heights[0] = rng.uniform(-1, 1)
    heights[n] = rng.uniform(-1, 1)
    step, disp = n, 1.0
    while step > 1:
        half = step // 2
        for i in range(half, n, step):
            mid = (heights[i - half] + heights[i + half]) / 2
            heights[i] = mid + rng.uniform(-disp, disp)
        step = half
        disp *= roughness
    lo, hi = min(heights), max(heights)
    span = (hi - lo) or 1.0
    return [base + amplitude * (heights[i] - lo) / span for i in range(width)]


def make_scene(seed):
    rng = random.Random(seed)
    height = SKY_H + LAND_H + WATER_H
    grid = [[" "] * WIDTH for _ in range(height)]
    horizon = SKY_H + LAND_H  # first water row

    # --- stars ---
    for _ in range(rng.randint(28, 48)):
        x, y = rng.randrange(WIDTH), rng.randrange(SKY_H + LAND_H - 2)
        grid[y][x] = rng.choice(".....''``+*")

    # --- moon (random phase and position) ---
    mx = rng.randint(8, WIDTH - 9)
    my = rng.randint(2, 5)
    r = rng.uniform(2.2, 3.2)
    phase = rng.uniform(-1.0, 1.0)  # -1 waning crescent .. 1 waxing crescent
    for dy in range(-4, 5):
        for dx in range(-8, 9):
            fx, fy = dx / 2.0, float(dy)  # chars are ~2x taller than wide
            if fx * fx + fy * fy <= r * r:
                # carve a crescent by subtracting an offset disc
                sx = fx - phase * r * 1.2
                lit = (sx * sx + fy * fy) > (r * r * abs(phase) * 0.9) or abs(phase) < 0.25
                y, x = my + dy, mx + dx
                if 0 <= y < SKY_H and 0 <= x < WIDTH:
                    grid[y][x] = "@" if lit else " "

    # --- mountain ridges, back to front ---
    layers = [
        (SKY_H - 6, 5.5, 0.55, "-"),   # far ridge
        (SKY_H - 3, 6.5, 0.60, "^"),   # mid ridge
        (SKY_H + 0, 6.0, 0.65, "#"),   # near ridge
    ]
    ridge_tops = [horizon] * WIDTH  # for reflections later
    for base, amp, rough, ch in layers:
        hs = ridge_heights(rng, WIDTH, base, amp, rough)
        for x in range(WIDTH):
            top = int(round(hs[x]))
            top = max(1, min(horizon - 1, top))
            ridge_tops[x] = min(ridge_tops[x], top)
            for y in range(top, horizon):
                grid[y][x] = ch

    # --- water ---
    moon_col = mx
    for wy in range(WATER_H):
        y = horizon + wy
        for x in range(WIDTH):
            # moonlight glitter path widens with depth
            glitter_w = 2 + wy * 2
            if abs(x - moon_col) <= glitter_w and rng.random() < 0.55:
                grid[y][x] = rng.choice("~=~-")
            elif rng.random() < 0.16:
                grid[y][x] = rng.choice("~-  ")
            else:
                grid[y][x] = " " if rng.random() < 0.5 else "_"

    # frame it
    top = "." + "-" * WIDTH + "."
    bottom = "'" + "-" * WIDTH + "'"
    body = ["|" + "".join(row) + "|" for row in grid]
    return "\n".join([top] + body + [bottom])


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else random.randrange(10**6)
    print(make_scene(seed))
    print(f"  seed: {seed}   (rerun with: python3 nightscape.py {seed})")
