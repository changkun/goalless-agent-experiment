#!/usr/bin/env python3
"""
ASCII Landscape Generator
Creates procedural landscapes with sky, terrain, and weather.
Each seed produces a unique, reproducible scene.

Usage: python3 ascii_landscape.py [seed]
"""

import random
import math
import sys

# ── Character palettes ──────────────────────────────────────────────

SKY = {
    "clear":  "  .·",
    "cloudy": "  .░▒",
    "night":  "  ·✦★",
}

SURFACE = {
    "mountain": "▲",
    "forest":   "♣♠",
    "desert":   "~",
    "ocean":    "≈≋",
    "plains":   "⌇\"",
}

BODY = {
    "mountain": "▁▂▃▄",
    "forest":   "▓█├╟",
    "desert":   "≈≋░▒",
    "ocean":    "~≈≋░",
    "plains":   "░▒▓┊",
}

DEEP = {
    "mountain": "█",
    "forest":   "╟",
    "desert":   "▓",
    "ocean":    "▁",
    "plains":   "╎",
}

WEATHER = {
    "rain": "│╎┊║",
    "snow": "*•·✧",
}


# ── Deterministic noise ─────────────────────────────────────────────

def _hash(n):
    n = ((n >> 16) ^ n) * 0x45d9f3b & 0xFFFFFFFF
    n = ((n >> 16) ^ n) * 0x45d9f3b & 0xFFFFFFFF
    return (n >> 16) ^ n & 0xFFFFFFFF


def noise1d(x, seed=0, scale=0.04):
    """1D value noise with smoothstep."""
    n = x * scale + seed * 13.37
    i = int(math.floor(n))
    f = n - i
    f = f * f * (3 - 2 * f)
    a = (_hash(i + seed * 997) & 0xFF) / 255.0
    b = (_hash(i + 1 + seed * 997) & 0xFF) / 255.0
    return a + (b - a) * f


def fbm(x, seed=0, octaves=4, scale=0.04, lac=2.0, gain=0.5):
    """Fractal Brownian Motion."""
    val = 0.0
    amp = 1.0
    freq = scale
    for o in range(octaves):
        val += noise1d(x, seed + o * 7919, freq) * amp
        amp *= gain
        freq *= lac
    return val


# ── Selectors ───────────────────────────────────────────────────────

def pick(seed, index, thresholds):
    """Pick from a list of (threshold, value) pairs."""
    r = noise1d(index, seed, scale=1.0)
    for thresh, val in thresholds:
        if r < thresh:
            return val
    return thresholds[-1][1]


# ── Main compose ────────────────────────────────────────────────────

def compose(width=80, height=24, seed=None):
    if seed is None:
        seed = random.randint(0, 999999)
    rng = random.Random(seed)

    biome   = pick(seed, 0, [(0.25, "mountain"), (0.50, "forest"),
                              (0.65, "desert"), (0.80, "plains"), (1.0, "ocean")])
    time    = pick(seed, 1, [(0.40, "clear"), (0.72, "cloudy"), (1.0, "night")])
    weather = pick(seed, 2, [(0.50, "none"), (0.78, "rain"), (1.0, "snow")])

    sky_chars     = SKY[time]
    surface_chars = SURFACE[biome]
    body_chars    = BODY[biome]
    deep_char     = DEEP[biome]
    weather_chars = WEATHER.get(weather, "")

    # ── Heightmaps ──────────────────────────────────────────────────
    # Surface position for each column (row index from top).
    # "sky_budget" = how many of the top rows belong to sky.
    sky_budget = height * 3 // 5  # ~60% sky, 40% terrain

    # Background silhouette: stays in upper part of sky_budget
    bg_surface = []
    for x in range(width):
        h = fbm(x, seed + 1111, octaves=3, scale=0.025)
        # Map to rows: background sits higher (less tall)
        row = int(sky_budget * 0.55 + h * sky_budget * 0.35)
        row = max(sky_budget // 4, min(row, sky_budget - 2))
        bg_surface.append(row)

    # Foreground silhouette: occupies lower part, more dramatic
    fg_surface = []
    for x in range(width):
        h = fbm(x, seed, octaves=5, scale=0.018)
        row = int(sky_budget * 0.70 + h * (height - sky_budget) * 0.9)
        row = max(bg_surface[x] + 2, min(row, height - 2))
        fg_surface.append(row)

    # ── Clouds (if cloudy) ──────────────────────────────────────────
    cloud_rows = {}
    if time == "cloudy":
        for x in range(width):
            c = fbm(x, seed + 5555, octaves=2, scale=0.06)
            if c > 0.52:
                cloud_rows.setdefault(int(c * 4) % 3 + 2, set()).add(x)

    # ── Render ───────────────────────────────────────────────────────
    canvas = []
    for y in range(height):
        row = []
        for x in range(width):
            bg = bg_surface[x]
            fg = fg_surface[x]

            if y < bg:
                # ──── Sky ────────────────────────────────────────
                ch = rng.choice(sky_chars)

                # Clouds
                if time == "cloudy" and y in cloud_rows and x in cloud_rows[y]:
                    ch = rng.choice("░▒▓")

                # Weather particles
                if weather != "none" and rng.random() < 0.08:
                    ch = rng.choice(weather_chars)

                # Sun
                if time == "clear":
                    sx = width * 3 // 4
                    sy = 3
                    dx, dy = abs(x - sx), abs(y - sy)
                    if dx + dy == 0:
                        ch = "☉"
                    elif dx + dy <= 2:
                        ch = rng.choice("· ")

                # Moon + stars
                if time == "night":
                    mx = width // 4
                    if abs(x - mx) <= 1 and y == 2:
                        ch = "☾" if x == mx else " "
                    elif y < bg - 2 and rng.random() < 0.01:
                        ch = rng.choice("✦★")

                row.append(ch)

            elif y < fg:
                # ──── Background terrain (distant, faded) ────────
                frac = (y - bg) / max(fg - bg, 1)
                if frac < 0.2:
                    ch = rng.choice(surface_chars)
                elif frac < 0.6:
                    ch = rng.choice(body_chars[:2])
                else:
                    ch = rng.choice(body_chars[2:])

                # Fade: swap dense for lighter
                ch = {"█": "▒", "▓": "░", "╟": "├", "▄": "▂"}.get(ch, ch)
                row.append(ch)

            elif y == fg:
                # ──── Foreground crest ───────────────────────────
                ch = rng.choice(surface_chars)
                row.append(ch)

            elif y < fg + 4:
                # ──── Foreground body (just below crest) ────────
                depth = y - fg
                ch = body_chars[min(depth, len(body_chars) - 1)]
                row.append(ch)

            else:
                # ──── Deep ground — sparse, mostly flat ──────────
                if rng.random() < 0.3:
                    ch = rng.choice(body_chars)
                else:
                    ch = deep_char
                row.append(ch)

        canvas.append("".join(row))

    # ── Border & title ───────────────────────────────────────────────
    top = "╔" + "═" * width + "╗"
    bot = "╚" + "═" * width + "╝"

    title = f" {biome.capitalize()} — {time}"
    if weather != "none":
        title += f", {weather}ing"
    title += f"  (seed {seed}) "
    header = "║" + title.center(width) + "║"

    output = [top, header]
    for line in canvas:
        output.append("║" + line + "║")
    output.append(bot)

    return "\n".join(output)


if __name__ == "__main__":
    width = 80
    height = 22

    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [seed]")
            sys.exit(1)
    else:
        seed = None

    print(compose(width, height, seed))
