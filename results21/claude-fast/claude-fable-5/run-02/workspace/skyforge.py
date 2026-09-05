#!/usr/bin/env python3
"""skyforge — invent a night sky.

Generates a fictional star chart as an SVG poster: a field of stars,
a handful of constellations traced between the brighter ones, each
given a pronounceable invented name. No dependencies.

Usage:
    python3 skyforge.py [seed] [-o out.svg]
"""

import math
import random
import sys

W, H = 900, 1200
MARGIN = 70

# --- name generation ---------------------------------------------------

ONSETS = ["", "b", "c", "d", "f", "g", "k", "l", "m", "n", "p", "r",
          "s", "t", "v", "z", "th", "ph", "ch", "br", "cr", "dr", "kr",
          "sk", "st", "tr", "vy", "zh"]
VOWELS = ["a", "e", "i", "o", "u", "ae", "ia", "ei", "ou", "y"]
CODAS = ["", "", "l", "n", "r", "s", "th", "x", "m", "sh", "nd", "rn"]

LATIN_TAILS = ["is", "us", "a", "ae", "or", "ix", "on", "um", "ara", "eus"]

def word(rng, syllables):
    parts = []
    for i in range(syllables):
        onset = rng.choice(ONSETS[1:]) if i == 0 else rng.choice(ONSETS)
        parts.append(onset + rng.choice(VOWELS))
    return "".join(parts) + rng.choice(CODAS)

def constellation_name(rng):
    base = word(rng, rng.choice([2, 2, 3]))
    name = (base + rng.choice(LATIN_TAILS)).capitalize()
    # occasional two-word "the X of Y" flavor, kept short
    if rng.random() < 0.25:
        epithet = rng.choice(["Minor", "Major", "Borealis", "Australis",
                              "Obscura", "Vagans", "Serena"])
        name = f"{name} {epithet}"
    return name

# --- sky generation ----------------------------------------------------

def make_stars(rng, n=420):
    stars = []
    for _ in range(n):
        x = rng.uniform(MARGIN * 0.4, W - MARGIN * 0.4)
        y = rng.uniform(MARGIN * 0.4, H - MARGIN * 0.4)
        # magnitude skewed heavily toward faint stars, like a real sky
        mag = rng.random() ** 3.2
        stars.append((x, y, mag))
    return stars

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def make_constellation(rng, stars, used):
    """Greedy walk between bright stars: pick a bright anchor, then hop
    to nearby unused bright stars, preferring gentle turns so the figure
    reads as a shape rather than a scribble."""
    bright = [s for s in stars if s[2] > 0.45 and id(s) not in used]
    if len(bright) < 5:
        return None
    path = [rng.choice(bright)]
    used.add(id(path[0]))
    heading = None
    for _ in range(rng.randint(4, 8)):
        cands = [s for s in bright if id(s) not in used
                 and 40 < dist(s, path[-1]) < 190]
        if not cands:
            break
        def score(s):
            d = dist(s, path[-1])
            if heading is None:
                return d
            ang = math.atan2(s[1] - path[-1][1], s[0] - path[-1][0])
            turn = abs(math.atan2(math.sin(ang - heading),
                                  math.cos(ang - heading)))
            return d + turn * 130
        nxt = min(cands, key=score)
        heading = math.atan2(nxt[1] - path[-1][1], nxt[0] - path[-1][0])
        path.append(nxt)
        used.add(id(nxt))
    return path if len(path) >= 4 else None

# --- rendering ---------------------------------------------------------

def render(seed, out):
    rng = random.Random(seed)
    stars = make_stars(rng)
    used = set()
    constellations = []
    attempts = 0
    while len(constellations) < 7 and attempts < 60:
        attempts += 1
        c = make_constellation(rng, stars, used)
        if c:
            constellations.append((constellation_name(rng), c))

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
               f'height="{H}" viewBox="0 0 {W} {H}">')
    svg.append('<defs><radialGradient id="sky" cx="50%" cy="35%" r="90%">'
               '<stop offset="0%" stop-color="#101a33"/>'
               '<stop offset="100%" stop-color="#05070f"/>'
               '</radialGradient></defs>')
    svg.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    # faint milky-way band: a wide translucent diagonal blur of dots
    band_angle = rng.uniform(-0.6, 0.6)
    for _ in range(900):
        t = rng.gauss(0, 90)
        u = rng.uniform(-H, H * 2)
        x = W / 2 + u * math.sin(band_angle) + t * math.cos(band_angle)
        y = H / 2 - u * math.cos(band_angle) + t * math.sin(band_angle)
        if 0 < x < W and 0 < y < H:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" '
                       f'r="{rng.uniform(0.3, 0.9):.2f}" fill="#aab6d8" '
                       f'opacity="{rng.uniform(0.04, 0.14):.2f}"/>')

    # constellation lines under the stars
    for _, path in constellations:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in path)
        svg.append(f'<polyline points="{pts}" fill="none" '
                   'stroke="#7f95c9" stroke-width="1" opacity="0.55"/>')

    # stars
    for x, y, mag in stars:
        r = 0.5 + mag * 2.6
        op = 0.35 + mag * 0.65
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
                   f'fill="#eef2ff" opacity="{op:.2f}"/>')
        if mag > 0.75:  # four-point twinkle on the brightest
            s = r * 3.2
            svg.append(f'<path d="M {x - s:.1f} {y:.1f} H {x + s:.1f} '
                       f'M {x:.1f} {y - s:.1f} V {y + s:.1f}" '
                       'stroke="#eef2ff" stroke-width="0.6" opacity="0.5"/>')

    # constellation labels near the figure's centroid
    for name, path in constellations:
        cx = sum(p[0] for p in path) / len(path)
        cy = sum(p[1] for p in path) / len(path)
        svg.append(f'<text x="{cx:.0f}" y="{cy - 14:.0f}" fill="#9db0dd" '
                   'font-family="Georgia, serif" font-style="italic" '
                   f'font-size="15" text-anchor="middle" opacity="0.85">'
                   f'{name}</text>')

    # title cartouche
    title = f"Sky no. {seed}"
    svg.append(f'<text x="{W / 2}" y="{H - 34}" fill="#c9d4f0" '
               'font-family="Georgia, serif" font-size="22" '
               f'text-anchor="middle" letter-spacing="6">{title.upper()}</text>')
    svg.append(f'<line x1="{W / 2 - 130}" y1="{H - 58}" x2="{W / 2 + 130}" '
               f'y2="{H - 58}" stroke="#5d6c96" stroke-width="0.7"/>')
    svg.append('</svg>')

    with open(out, "w") as f:
        f.write("\n".join(svg))
    return [name for name, _ in constellations]

if __name__ == "__main__":
    args = sys.argv[1:]
    out = "sky.svg"
    if "-o" in args:
        i = args.index("-o")
        out = args[i + 1]
        del args[i:i + 2]
    seed = int(args[0]) if args else random.randrange(10000)
    names = render(seed, out)
    print(f"seed {seed} -> {out}")
    for n in names:
        print(f"  · {n}")
