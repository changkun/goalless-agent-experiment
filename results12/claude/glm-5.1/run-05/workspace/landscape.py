#!/usr/bin/env python3
"""
ASCII Landscape Generator
Generates a procedural landscape scene that changes based on the current hour.
Includes mountains, trees, water, sky, moon/sun, and animated weather.

Run: python3 landscape.py [--animate] [--storm] [--night] [--dawn] [--dusk]
"""

import random
import time
import sys
import math
from datetime import datetime

# ─── Palette ───────────────────────────────────────────────────────────────

SKY_CHARS = {
    "night":  { 0: "✦", 1: "·", 2: " ", 3: " " },
    "dawn":   { 0: "☀", 1: "~", 2: "░", 3: " " },
    "day":    { 0: "☀", 1: "☁", 2: "░", 3: " " },
    "dusk":   { 0: "☀", 1: "~", 2: "░", 3: " " },
}

MOUNTAIN_CHARS = ["▲", "△", "▂", "▃", "▄", "▅", "▆", "▇"]
TREE_CHARS = ["🌲", "🌳", "🌴", "🌿", "🍀"]
WATER_CHARS = ["≈", "~", "≋", "〰", "﹏"]
CLOUD_CHARS = ["☁", "⛅", "🌥", " nier"]
RAIN_CHARS = ["⋮", "⋱", "┊", "╎"]
SNOW_CHARS = ["❄", "❅", "❆", "•", "∘"]

# Color codes
class C:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"

    # Sky colors
    NIGHT_SKY   = "\033[38;5;17m"
    DAWN_SKY    = "\033[38;5;131m"
    DAY_SKY     = "\033[38;5;117m"
    DUSK_SKY    = "\033[38;5;162m"

    # Ground colors
    MOUNTAIN_FAR = "\033[38;5;240m"
    MOUNTAIN_MID = "\033[38;5;244m"
    MOUNTAIN_NEAR= "\033[38;5;250m"
    TREE_GREEN   = "\033[38;5;28m"
    TREE_DARK    = "\033[38;5;22m"
    WATER_BLUE   = "\033[38;5;39m"
    WATER_DEEP   = "\033[38;5;25m"
    GROUND       = "\033[38;5;137m"
    GROUND_DARK  = "\033[38;5;130m"

    MOON_GLOW = "\033[38;5;229m"
    SUN_GLOW  = "\033[38;5;220m"
    STAR      = "\033[38;5;255m"
    RAIN      = "\033[38;5;111m"
    SNOW      = "\033[38;5;254m"


# ─── Procedural generation ─────────────────────────────────────────────────

def time_of_day(hour=None):
    if hour is None:
        hour = datetime.now().hour
    if 0 <= hour < 5:   return "night"
    if 5 <= hour < 7:   return "dawn"
    if 7 <= hour < 17:  return "day"
    if 17 <= hour < 20: return "dusk"
    return "night"


def sky_color(tod):
    return {
        "night": C.NIGHT_SKY, "dawn": C.DAWN_SKY,
        "day": C.DAY_SKY, "dusk": C.DUSK_SKY
    }[tod]


def generate_heightmap(width, peaks, roughness=0.6):
    """Generate a 1D heightmap using midpoint displacement."""
    h = [0.0] * width
    for cx, ch in peaks:
        for x in range(width):
            dist = abs(x - cx) / (width * 0.3)
            influence = max(0, ch * (1 - dist**2))
            h[x] = max(h[x], influence)
    # add some roughness
    for x in range(width):
        h[x] += random.gauss(0, roughness * 0.1)
        h[x] = max(0, min(1, h[x]))
    # smooth
    for _ in range(3):
        h = [(h[(x-1)%width] + h[x] + h[(x+1)%width]) / 3 for x in range(width)]
    return h


def generate_mountains(width, layers=3):
    """Generate multiple mountain layers."""
    mountains = []
    for i in range(layers):
        n_peaks = random.randint(2, 4)
        height_scale = 0.4 + i * 0.2
        peaks = [(random.randint(0, width), random.uniform(0.3, height_scale))
                 for _ in range(n_peaks)]
        roughness = 0.4 + i * 0.3
        h = generate_heightmap(width, peaks, roughness)
        mountains.append((h, i))
    return mountains


def generate_trees(width, count, ground_level):
    """Place trees along the ground."""
    trees = []
    for _ in range(count):
        x = random.randint(2, width - 3)
        tree_type = random.choice(TREE_CHARS)
        trees.append((x, tree_type))
    return sorted(trees, key=lambda t: t[0])


def generate_stars(width, height, count):
    """Place stars in the sky."""
    stars = []
    for _ in range(count):
        x = random.randint(0, width - 1)
        y = random.randint(0, max(1, height // 3))
        brightness = random.choice(["✦", "·", "⋆", "✧", "·"])
        twinkle = random.random()
        stars.append((x, y, brightness, twinkle))
    return stars


def generate_clouds(width, count):
    """Generate cloud shapes."""
    clouds = []
    for _ in range(count):
        x = random.randint(0, width - 10)
        y = random.randint(2, 8)
        shape = random.choice([" ☁  ☁☁ ", " ☁☁☁ ", "  ☁☁ ☁", "☁☁☁☁☁"])
        speed = random.uniform(0.3, 1.5)
        clouds.append({"x": x, "y": y, "shape": shape, "speed": speed, "orig_x": x})
    return clouds


# ─── Rendering ──────────────────────────────────────────────────────────────

WIDTH = 72
HEIGHT = 26

def render_frame(tod, mountains, trees, stars, clouds, raindrops, snowflakes,
                 tick, ground_y=18, water_y=21):
    """Render one frame of the landscape."""
    buf = [[(" ", "") for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # ── Sky ──
    sc = sky_color(tod)
    for y in range(ground_y):
        for x in range(WIDTH):
            buf[y][x] = (" ", sc)

    # ── Stars (night/dusk/dawn) ──
    if tod in ("night", "dawn", "dusk"):
        for sx, sy, brightness, twinkle in stars:
            if 0 <= sy < ground_y and 0 <= sx < WIDTH:
                # twinkle effect
                phase = math.sin(tick * 0.1 + twinkle * 10) * 0.5 + 0.5
                if phase > 0.3:
                    color = C.STAR if tod == "night" else (C.DAWN_SKY if tod == "dawn" else C.DUSK_SKY)
                    buf[sy][sx] = (brightness, color)

    # ── Sun / Moon ──
    if tod == "night":
        # Moon
        mx = WIDTH // 2 + int(math.sin(tick * 0.02) * 8)
        my = 4 + int(math.cos(tick * 0.015) * 2)
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                px, py = mx + dx, my + dy
                if 0 <= py < ground_y and 0 <= px < WIDTH:
                    if dx*dx + dy*dy <= 4:
                        buf[py][px] = ("☽", C.MOON_GLOW)
    elif tod in ("dawn", "dusk"):
        # Sun at horizon
        sx = WIDTH // 2 + int(math.sin(tick * 0.01) * 5)
        sy = ground_y - 3 if tod == "dawn" else ground_y - 2
        for dy in range(-2, 1):
            for dx in range(-3, 4):
                px, py = sx + dx, sy + dy
                if 0 <= py < ground_y and 0 <= px < WIDTH:
                    dist = (dx**2 + dy**2) ** 0.5
                    if dist < 3:
                        buf[py][px] = ("☀", C.SUN_GLOW)
    else:
        # Day sun high
        sx = WIDTH // 2 + int(math.sin(tick * 0.02) * 10)
        sy = 3 + int(math.cos(tick * 0.015) * 2)
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                px, py = sx + dx, sy + dy
                if 0 <= py < ground_y and 0 <= px < WIDTH:
                    if dx*dx + dy*dy <= 3:
                        buf[py][px] = ("☀", C.SUN_GLOW)

    # ── Mountains ──
    mcolors = [C.MOUNTAIN_FAR, C.MOUNTAIN_MID, C.MOUNTAIN_NEAR]
    for heightmap, layer in mountains:
        color = mcolors[layer % len(mcolors)]
        peak_chars = ["▂", "▃", "▄", "▅", "▆", "▇", "█"]
        for x in range(WIDTH):
            h = heightmap[x]
            mheight = int(h * (6 + layer * 2))
            for dy in range(mheight):
                y = ground_y - 1 - dy
                if 0 <= y < ground_y:
                    if dy == mheight - 1:
                        ch = "▲" if h > 0.5 else "▂"
                    elif dy == 0:
                        ch = "▃"
                    else:
                        ch = peak_chars[min(dy, len(peak_chars)-1)]
                    buf[y][x] = (ch, color)

    # ── Ground ──
    for x in range(WIDTH):
        for y in range(ground_y, water_y):
            ch = "▓" if y == ground_y else ("▒" if y < ground_y + 2 else "░")
            buf[y][x] = (ch, C.GROUND if y < ground_y + 2 else C.GROUND_DARK)

    # ── Trees ──
    for tx, tree_char in trees:
        ty = ground_y - 1
        if 0 <= ty < HEIGHT and 0 <= tx < WIDTH - 1:
            buf[ty][tx] = (tree_char, C.TREE_GREEN)
            if ty + 1 < HEIGHT:
                buf[ty+1][tx] = ("│", C.TREE_DARK)

    # ── Water ──
    for y in range(water_y, HEIGHT):
        for x in range(WIDTH):
            wave = math.sin(x * 0.3 + tick * 0.15) * 0.5 + 0.5
            if wave > 0.6:
                ch = "≋"
            elif wave > 0.3:
                ch = "≈"
            else:
                ch = "~"
            color = C.WATER_BLUE if y < water_y + 2 else C.WATER_DEEP
            buf[y][x] = (ch, color)

    # ── Clouds ──
    for cloud in clouds:
        cx = int(cloud["orig_x"] + cloud["speed"] * tick) % WIDTH
        cy = cloud["y"]
        shape = cloud["shape"]
        for i, ch in enumerate(shape):
            px = (cx + i) % WIDTH
            if 0 <= cy < ground_y:
                if ch != " ":
                    buf[cy][px] = (ch, "\033[38;5;252m")

    # ── Rain ──
    if raindrops:
        for rx, ry in raindrops:
            if 0 <= ry < HEIGHT and 0 <= rx < WIDTH:
                buf[ry][rx] = (random.choice(RAIN_CHARS), C.RAIN)

    # ── Snow ──
    if snowflakes:
        for sx, sy in snowflakes:
            if 0 <= sy < HEIGHT and 0 <= sx < WIDTH:
                buf[sy][sx] = (random.choice(SNOW_CHARS), C.SNOW)

    # ── Compose output ──
    lines = []
    for row in buf:
        line = ""
        last_color = ""
        for ch, color in row:
            if color != last_color:
                line += color
                last_color = color
            line += ch
        line += C.RESET
        lines.append(line)

    return "\n".join(lines)


def update_particles(raindrops, snowflakes, is_rain, is_snow, tick):
    """Update rain/snow particle positions."""
    if is_rain:
        # Add new drops
        for _ in range(random.randint(1, 3)):
            raindrops.append([random.randint(0, WIDTH-1), random.randint(0, 4)])
        # Move drops down
        new_drops = []
        for drop in raindrops:
            drop[0] += random.choice([-1, 0, 0, 1])  # slight wind
            drop[1] += 2  # rain falls fast
            if drop[1] < HEIGHT and 0 <= drop[0] < WIDTH:
                new_drops.append(drop)
        raindrops[:] = new_drops

    if is_snow:
        for _ in range(random.randint(0, 2)):
            snowflakes.append([random.randint(0, WIDTH-1), random.randint(0, 3)])
        new_flakes = []
        for flake in snowflakes:
            flake[0] += random.choice([-1, 0, 1])  # drift
            flake[1] += 1  # snow falls slowly
            if flake[1] < HEIGHT and 0 <= flake[0] < WIDTH:
                new_flakes.append(flake)
        snowflakes[:] = new_flakes


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    animate = "--animate" in sys.argv
    force_weather = None
    force_tod = None

    if "--storm" in sys.argv:
        force_weather = "rain"
    elif "--snow" in sys.argv:
        force_weather = "snow"
    if "--night" in sys.argv:
        force_tod = "night"
    elif "--dawn" in sys.argv:
        force_tod = "dawn"
    elif "--dusk" in sys.argv:
        force_tod = "dusk"
    elif "--day" in sys.argv:
        force_tod = "day"

    tod = force_tod or time_of_day()
    random.seed(42)  # consistent landscapes

    mountains = generate_mountains(WIDTH, layers=3)
    trees = generate_trees(WIDTH, random.randint(8, 14), 18)
    stars = generate_stars(WIDTH, HEIGHT, random.randint(25, 50))
    clouds = generate_clouds(WIDTH, random.randint(2, 5))

    raindrops = []
    snowflakes = []
    is_rain = force_weather == "rain" or (force_weather is None and tod in ("dawn", "dusk") and random.random() > 0.6)
    is_snow = force_weather == "snow" or (force_weather is None and tod == "night" and random.random() > 0.7)

    # Title
    title_colors = {
        "night": "\033[38;5;111m",
        "dawn": "\033[38;5;215m",
        "day": "\033[38;5;226m",
        "dusk": "\033[38;5;202m",
    }
    tc = title_colors[tod]
    print()
    print(f"     {tc}{C.BOLD}✦  A S C I I   L A N D S C A P E  ✦{C.RESET}")
    print(f"     {tc}{C.DIM}  Time: {tod.upper():>5}  │  Weather: {'🌧 Rain' if is_rain else ('❄ Snow' if is_snow else '☀ Clear')}{C.RESET}")
    print(f"     {'─' * 42}")
    print()

    tick = 0
    if animate:
        print("\033[?25l")  # hide cursor
        try:
            while True:
                frame = render_frame(tod, mountains, trees, stars, clouds,
                                     raindrops, snowflakes, tick)
                # Move cursor to top of landscape area
                sys.stdout.write(f"\033[5H{frame}")
                sys.stdout.flush()

                update_particles(raindrops, snowflakes, is_rain, is_snow, tick)
                tick += 1
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"\033[?25h{C.RESET}")  # show cursor
            print("\n\n     Landscape fades into memory... 🌿")
    else:
        frame = render_frame(tod, mountains, trees, stars, clouds,
                             raindrops, snowflakes, tick)
        print(frame)
        print()
        print(f"     {C.DIM}Tip: use --animate for live animation,")
        print(f"           --storm / --snow for weather,")
        print(f"           --night / --dawn / --dusk / --day for time{C.RESET}")
        print()


if __name__ == "__main__":
    main()
