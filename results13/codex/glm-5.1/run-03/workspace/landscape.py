#!/usr/bin/env python3
"""Procedural ASCII art landscape generator."""

import random
import math
import sys

SCREEN_W = 72
SCREEN_H = 22

def noise(x, seed=0):
    """Simple hash-based value noise."""
    n = int(x * 173 + seed * 37) & 0x7FFFFFFF
    n = (n << 13) ^ n
    return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0

def smooth_noise(x, seed=0):
    """Smoothed noise with interpolation."""
    ix = int(math.floor(x))
    fx = x - ix
    fx = fx * fx * (3 - 2 * fx)  # smoothstep
    a = noise(ix, seed)
    b = noise(ix + 1, seed)
    return a + (b - a) * fx

def fbm(x, octaves=4, seed=0):
    """Fractal Brownian motion."""
    val = 0.0
    amp = 1.0
    freq = 1.0
    for _ in range(octaves):
        val += smooth_noise(x * freq, seed) * amp
        amp *= 0.5
        freq *= 2.0
    return val

def generate_terrain(width, seed):
    """Generate a terrain heightmap."""
    heights = []
    for x in range(width):
        h = fbm(x * 0.04, octaves=5, seed=seed)
        heights.append(h)
    # Normalize to 0-1
    lo, hi = min(heights), max(heights)
    return [(h - lo) / (hi - lo) if hi > lo else 0.5 for h in heights]

def generate_mountains(width, seed, scale=0.35):
    """Generate mountain silhouette."""
    heights = []
    for x in range(width):
        h = fbm(x * 0.025, octaves=4, seed=seed) * scale
        h += fbm(x * 0.06, octaves=3, seed=seed + 99) * scale * 0.4
        heights.append(max(0, h))
    return heights

def pick_tree():
    """Return a random tree ASCII shape (3 lines)."""
    trees = [
        ["   /\\   ", "  /  \\  ", "  ||  "],
        ["  /|\\  ", " /|||\\ ", "  ||  "],
        ["   ^^  ", "  /|\\  ", "   |   "],
        ["  /\\  ", " /  \\ ", " || "],
        ["  ^  ", " /|\\ ", "/|||\\", "  |  "],
    ]
    return random.choice(trees)

def build_sky(height, terrain_h, total_h):
    """Build sky row with stars and moon."""
    row = []
    depth = total_h - height
    star_chance = 0.04 if depth > 3 else 0.01
    for x in range(SCREEN_W):
        if random.random() < star_chance:
            row.append(random.choice(["·", "✦", "✧", "*", "⋆", "•"]))
        else:
            row.append(" ")
    return "".join(row)

def render(seed=None):
    """Render a complete landscape scene."""
    if seed is None:
        seed = random.randint(0, 99999)

    random.seed(seed)
    terrain = generate_terrain(SCREEN_W, seed)
    mountains = generate_mountains(SCREEN_W, seed + 42, scale=0.3)
    
    # Moon position
    moon_x = random.randint(10, SCREEN_W - 15)
    moon_y = random.randint(1, 4)
    
    canvas = []
    
    # Ground line (where terrain meets sky)
    ground_row = int(SCREEN_H * 0.7)
    
    for y in range(SCREEN_H):
        row = []
        for x in range(SCREEN_W):
            row_num = SCREEN_H - 1 - y  # 0 = bottom
            
            # Moon
            if (x - moon_x)**2 + (y - moon_y)**2 <= 9:
                if (x - moon_x)**2 + (y - moon_y)**2 <= 4:
                    row.append("░")
                else:
                    row.append("░")
                continue
            
            # Stars
            if row_num > ground_row + 2:
                if random.random() < 0.03:
                    row.append(random.choice(["·", "✦", ".", "*"]))
                    continue
            
            # Mountains (background)
            m_height = mountains[x]
            m_row = ground_row - int(m_height * SCREEN_H * 0.5)
            if row_num >= m_row and row_num <= ground_row:
                depth = (row_num - m_row)
                if row_num == m_row:
                    row.append("░")
                elif depth < 3:
                    row.append("▒")
                else:
                    row.append("▓")
                continue
            
            # Sky
            if row_num > ground_row:
                row.append(" ")
                continue
            
            # Terrain / ground
            t = terrain[x]
            terrain_row = ground_row - int(t * 4)
            
            if row_num == ground_row or (row_num >= terrain_row and row_num <= ground_row):
                if row_num == ground_row:
                    row.append(random.choice(["▓", "█"]))
                elif row_num >= ground_row - 1:
                    row.append(random.choice(["▒", "░"]))
                elif row_num >= ground_row - 2:
                    row.append(random.choice([",", ";", "~"]))
                else:
                    row.append(random.choice([" ", "."]))
            elif row_num < terrain_row:
                # Above terrain - sky
                row.append(" ")
            else:
                row.append(" ")
        
        canvas.append("".join(row))
    
    # Add some trees on the ground
    tree_positions = sorted(random.sample(range(5, SCREEN_W - 10), random.randint(3, 7)))
    ground_y = ground_row
    
    result = []
    for y, line in enumerate(canvas):
        result.append(list(line))
    
    for tx in tree_positions:
        tree = pick_tree()
        tree_h = len(tree)
        tree_w = len(tree[0])
        # Place tree above ground
        start_y = ground_y - tree_h
        for ty, tree_line in enumerate(tree):
            for tx_off, ch in enumerate(tree_line):
                py = start_y + ty
                px = tx - tree_w // 2 + tx_off
                if 0 <= py < SCREEN_H and 0 <= px < SCREEN_W:
                    if ch != " ":
                        result[py][px] = ch
    
    # Add water at the bottom
    for y in range(ground_row + 1, SCREEN_H):
        for x in range(SCREEN_W):
            r = random.random()
            if r < 0.3:
                result[y][x] = "≈"
            elif r < 0.6:
                result[y][x] = "~"
            elif r < 0.8:
                result[y][x] = "〜"
            else:
                result[y][x] = " "
    
    # Build final output
    lines = ["".join(r) for r in result]
    
    # Frame it
    top = "╔" + "═" * SCREEN_W + "╗"
    bot = "╚" + "═" * SCREEN_W + "╝"
    framed = [top] + ["║" + l + "║" for l in lines] + [bot]
    
    # Title
    title = f"  Landscape #{seed}  "
    title_line = "╠" + title.center(SCREEN_W, "═") + "╣"
    framed.insert(1, title_line)
    
    return "\n".join(framed)

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for i in range(count):
        seed = random.randint(0, 99999) if len(sys.argv) <= 2 else int(sys.argv[2]) + i
        print(render(seed))
        if i < count - 1:
            print()

if __name__ == "__main__":
    main()
