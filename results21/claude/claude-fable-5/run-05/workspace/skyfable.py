#!/usr/bin/env python3
"""
skyfable.py — a procedural night sky with invented constellations.

Every run invents a sky that has never existed: stars are scattered,
constellations are grown star-to-star, and each one is given a name
and a one-line myth. Output is a PNG written by a hand-rolled encoder
(zlib + struct only — no dependencies), plus the myths on stdout.

Usage:
    python3 skyfable.py [seed]
"""

import math
import random
import struct
import sys
import zlib

W, H = 1200, 800


# ---------------------------------------------------------------- PNG writer

def write_png(path, width, height, pixels):
    """pixels: bytearray of RGB triples, row-major."""
    def chunk(tag, data):
        payload = tag + data
        return (struct.pack(">I", len(data)) + payload
                + struct.pack(">I", zlib.crc32(payload)))

    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filter type: None
        raw += pixels[y * stride:(y + 1) * stride]

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


# ---------------------------------------------------------------- drawing

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, r, g, b):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b

    def add(self, x, y, r, g, b):
        """Additive blend, clamped — light accumulates like real exposure."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i]     = min(255, self.px[i] + r)
            self.px[i + 1] = min(255, self.px[i + 1] + g)
            self.px[i + 2] = min(255, self.px[i + 2] + b)

    def glow(self, cx, cy, radius, r, g, b):
        """Soft gaussian-ish dot."""
        rr = int(radius * 3) + 1
        for dy in range(-rr, rr + 1):
            for dx in range(-rr, rr + 1):
                d2 = dx * dx + dy * dy
                f = math.exp(-d2 / (2 * radius * radius))
                if f > 0.01:
                    self.add(int(cx) + dx, int(cy) + dy,
                             int(r * f), int(g * f), int(b * f))

    def line(self, x0, y0, x1, y1, r, g, b, alpha=1.0):
        """Anti-aliased-ish line drawn as many faint dots."""
        steps = max(2, int(math.hypot(x1 - x0, y1 - y0)))
        for i in range(steps + 1):
            t = i / steps
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            self.add(int(x), int(y), int(r * alpha), int(g * alpha), int(b * alpha))
            self.add(int(x) + 1, int(y), int(r * alpha * .4), int(g * alpha * .4), int(b * alpha * .4))
            self.add(int(x), int(y) + 1, int(r * alpha * .4), int(g * alpha * .4), int(b * alpha * .4))


# ---------------------------------------------------------------- sky pieces

def paint_sky(c, rng):
    """Vertical gradient with a hint of horizon glow and faint nebulosity."""
    top = (4, 6, 20)
    bottom = (18, 12, 38)
    # two random nebula blobs, very faint
    nebulae = [(rng.uniform(0, W), rng.uniform(0, H * 0.7),
                rng.uniform(150, 320),
                rng.choice([(30, 12, 40), (10, 25, 45), (35, 18, 22)]))
               for _ in range(3)]
    for y in range(H):
        t = y / H
        r = top[0] + (bottom[0] - top[0]) * t
        g = top[1] + (bottom[1] - top[1]) * t
        b = top[2] + (bottom[2] - top[2]) * t
        for x in range(W):
            rr, gg, bb = r, g, b
            for nx, ny, nr, (cr, cg, cb) in nebulae:
                d2 = (x - nx) ** 2 + (y - ny) ** 2
                f = math.exp(-d2 / (2 * nr * nr))
                rr += cr * f
                gg += cg * f
                bb += cb * f
            i = (y * W + x) * 3
            c.px[i], c.px[i + 1], c.px[i + 2] = int(min(255, rr)), int(min(255, gg)), int(min(255, bb))


def star_color(rng):
    """Rough stellar temperature palette: blue-white, white, gold, ember."""
    kind = rng.random()
    if kind < 0.45:
        return (200, 215, 255)
    if kind < 0.8:
        return (255, 250, 240)
    if kind < 0.95:
        return (255, 220, 160)
    return (255, 170, 130)


def scatter_stars(c, rng, n=420):
    stars = []
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        mag = rng.random() ** 2.5           # most stars are dim
        radius = 0.6 + mag * 2.4
        r, g, b = star_color(rng)
        f = 0.25 + mag * 0.75
        c.glow(x, y, radius, int(r * f), int(g * f), int(b * f))
        if mag > 0.35:                      # only the bright ones join constellations
            stars.append((x, y, mag))
    return stars


def grow_constellation(stars, used, rng):
    """Pick a bright seed star and walk to nearby unused stars."""
    candidates = [i for i in range(len(stars)) if i not in used]
    if not candidates:
        return []
    seed = max(rng.sample(candidates, min(12, len(candidates))),
               key=lambda i: stars[i][2])
    chain = [seed]
    used.add(seed)
    length = rng.randint(4, 8)
    while len(chain) < length:
        cx, cy, _ = stars[chain[-1]]
        near = sorted(
            (i for i in range(len(stars)) if i not in used
             and 40 < math.hypot(stars[i][0] - cx, stars[i][1] - cy) < 170),
            key=lambda i: math.hypot(stars[i][0] - cx, stars[i][1] - cy))
        if not near:
            break
        nxt = near[0] if rng.random() < 0.7 else rng.choice(near[:3])
        chain.append(nxt)
        used.add(nxt)
    return chain if len(chain) >= 3 else []


# ---------------------------------------------------------------- naming

SYLLABLES = ["al", "be", "cor", "dra", "el", "fen", "gal", "hy", "ith", "ka",
             "lor", "mir", "noc", "or", "pha", "qui", "ras", "sel", "tha",
             "um", "vel", "wyn", "xa", "yr", "zeph"]

EPITHETS = ["the Wanderer", "the Lantern-Bearer", "the Unfinished Bridge",
            "the Sleeping River", "the Cartographer", "the Borrowed Crown",
            "the Moth-Queen", "the Last Ferryman", "the Patient Thief",
            "the Salt Archivist", "the Gardener of Echoes", "the Broken Compass"]

MYTHS = [
    "said to appear only to travelers who have forgotten the way home, and to point somewhere better.",
    "hung in the sky as payment for a debt the moon still refuses to discuss.",
    "each star a lamp left burning by someone who meant to come right back.",
    "climbs a little higher every century; no one remembers what it is climbing toward.",
    "the old maps drew it upside down, and some sailors swear it works better that way.",
    "keeps a single secret, and dims slightly whenever someone guesses close.",
    "was once two constellations that argued so long they grew together.",
    "children are told it counts them at night; adults are told nothing, which worries them more.",
    "marks the spot where the sky was mended, if you believe the sky was ever torn.",
    "follows the harvest moon at a polite distance, out of respect or fear.",
    "is missing one star, which is said to be down here somewhere, living quietly.",
    "grants no wishes but listens to all of them, which the old stories say is rarer.",
]


def invent_name(rng, epithet):
    n = "".join(rng.choice(SYLLABLES) for _ in range(rng.randint(2, 3))).capitalize()
    return f"{n}, {epithet}"


# ---------------------------------------------------------------- main

def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10 ** 6)
    rng = random.Random(seed)

    c = Canvas(W, H)
    paint_sky(c, rng)
    stars = scatter_stars(c, rng)

    used = set()
    fables = []
    myth_deck = rng.sample(MYTHS, len(MYTHS))
    epithet_deck = rng.sample(EPITHETS, len(EPITHETS))
    for _ in range(rng.randint(4, 6)):
        chain = grow_constellation(stars, used, rng)
        if not chain:
            continue
        for a, b in zip(chain, chain[1:]):
            x0, y0, _ = stars[a]
            x1, y1, _ = stars[b]
            c.line(x0, y0, x1, y1, 120, 150, 200, alpha=0.35)
        for i in chain:  # re-brighten member stars so they sit atop the lines
            x, y, mag = stars[i]
            c.glow(x, y, 1.2 + mag * 1.5, 90, 100, 130)
        name = invent_name(rng, epithet_deck.pop())
        fables.append((name, len(chain), myth_deck.pop()))

    out = f"sky_{seed}.png"
    write_png(out, W, H, c.px)

    print(f"seed {seed} → {out}\n")
    print("Tonight's sky contains:\n")
    for name, n, myth in fables:
        print(f"  ✦ {name} ({n} stars)")
        print(f"    {myth}\n")


if __name__ == "__main__":
    main()
