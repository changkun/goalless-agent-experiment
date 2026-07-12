#!/usr/bin/env python3
"""
✦ G A L A X Y   G E N E R A T O R ✦
─────────────────────────────────────
Generates unique ASCII art galaxies using cellular automata seeds.
Each run produces a different cosmic structure.
"""

import random
import math
import sys

PALETTE = [
    "\033[38;5;147m",  # lavender
    "\033[38;5;183m",  # light purple
    "\033[38;5;225m",  # pink
    "\033[38;5;220m",  # gold
    "\033[38;5;229m",  # light gold
    "\033[38;5;254m",  # white
    "\033[38;5;81m",   # sky blue
    "\033[38;5;45m",   # cyan
]
RESET = "\033[0m"
DIM = "\033[2m"

GALAXY_CHARS = "·✦⋆✧∙∘○◌●◎⊕⊛✶✷✸✹"


def galaxy(width=72, height=28):
    """Generate a spiral galaxy ASCII art."""
    canvas = [[" " for _ in range(width)] for _ in range(height)]
    colors = [["" for _ in range(width)] for _ in range(height)]

    cx, cy = width // 2, height // 2
    arms = random.randint(2, 5)
    tightness = random.uniform(0.15, 0.4)
    tilt = random.uniform(-0.3, 0.3)

    # Draw spiral arms
    for arm in range(arms):
        arm_offset = (2 * math.pi / arms) * arm
        for t in range(200):
            theta = tightness * t + arm_offset
            r = 0.3 + t * 0.08
            # Apply tilt (projection)
            x = cx + r * math.cos(theta + tilt)
            y = cy + r * math.sin(theta) * 0.55  # flatten for inclination

            ix, iy = int(x), int(y)
            if 0 <= ix < width and 0 <= iy < height:
                # Density decreases with radius
                density = max(0, 1 - r / (max(width, height) * 0.45))
                if random.random() < density:
                    char_idx = min(int(r * 0.8), len(GALAXY_CHARS) - 1)
                    ch = GALAXY_CHARS[char_idx]
                    color = PALETTE[min(int(r * 0.3), len(PALETTE) - 1)]
                    canvas[iy][ix] = ch
                    colors[iy][ix] = color

                    # Scatter nearby stars
                    for _ in range(random.randint(1, 3)):
                        dx = random.gauss(0, 0.8 + r * 0.05)
                        dy = random.gauss(0, 0.5 + r * 0.03)
                        sx, sy = int(x + dx), int(y + dy)
                        if 0 <= sx < width and 0 <= sy < height and canvas[sy][sx] == " ":
                            canvas[sy][sx] = random.choice("·.⋅∘")
                            colors[sy][sx] = random.choice(PALETTE[:4])

    # Sprinkle background stars
    for _ in range(width * height // 30):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        if canvas[y][x] == " ":
            canvas[y][x] = random.choice("·.⋅")
            colors[y][x] = random.choice(PALETTE[5:])

    # Bright core
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < height and 0 <= nx < width:
                dist = math.sqrt(dx * dx + dy * dy * 3)
                if dist < 2:
                    canvas[ny][nx] = random.choice("◎⊕⊛✶")
                    colors[ny][nx] = PALETTE[random.randint(3, 5)]

    # Render
    lines = []
    for y in range(height):
        row = ""
        for x in range(width):
            ch = canvas[y][x]
            if ch != " ":
                row += colors[y][x] + ch + RESET
            else:
                row += " "
        lines.append(row)

    return "\n".join(lines)


def main():
    print()
    print(f"  {DIM}Generating galaxy from cellular seed...{RESET}")
    print()

    seed = random.randint(0, 999999)
    random.seed(seed)

    art = galaxy()
    print(art)
    print()
    print(f"  {DIM}Galaxy seed: {seed}{RESET}")
    print(f"  {DIM}Each seed produces a unique galaxy ✧{RESET}")
    print()


if __name__ == "__main__":
    main()
