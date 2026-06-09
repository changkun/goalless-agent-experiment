#!/usr/bin/env python3
"""Flow field generative art — pure stdlib, outputs SVG.

Particles drift through a Perlin-style gradient noise field. Each trail
is stroked with a color picked from its average heading, so the palette
emerges from the field itself rather than being painted on.
"""

import colorsys
import math
import random
import struct
import zlib

# ---------------------------------------------------------------- noise

class PerlinNoise:
    """Classic 2D gradient noise with a shuffled permutation table."""

    def __init__(self, seed):
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self.perm = p + p
        # unit gradient vectors at random angles
        self.grads = [
            (math.cos(a), math.sin(a))
            for a in (rng.uniform(0, 2 * math.pi) for _ in range(256))
        ]

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _grad_dot(self, ix, iy, x, y):
        g = self.grads[self.perm[self.perm[ix & 255] + (iy & 255)] & 255]
        return g[0] * (x - ix) + g[1] * (y - iy)

    def noise(self, x, y):
        x0, y0 = math.floor(x), math.floor(y)
        u, v = self._fade(x - x0), self._fade(y - y0)
        n00 = self._grad_dot(x0, y0, x, y)
        n10 = self._grad_dot(x0 + 1, y0, x, y)
        n01 = self._grad_dot(x0, y0 + 1, x, y)
        n11 = self._grad_dot(x0 + 1, y0 + 1, x, y)
        nx0 = n00 + u * (n10 - n00)
        nx1 = n01 + u * (n11 - n01)
        return nx0 + v * (nx1 - nx0)  # roughly [-1, 1]

    def octaves(self, x, y, n=3, lacunarity=2.0, gain=0.5):
        total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
        for _ in range(n):
            total += amp * self.noise(x * freq, y * freq)
            norm += amp
            amp *= gain
            freq *= lacunarity
        return total / norm


# ---------------------------------------------------------------- field

W, H = 1200, 900
SEED = 20260608
SCALE = 0.0035          # noise zoom: smaller = broader swirls
CURL = 2.6              # how many half-turns the angle range spans
STEP = 3.0              # particle step length in px
STEPS = 140             # max steps per trail
N_PARTICLES = 2600

noise = PerlinNoise(SEED)
rng = random.Random(SEED + 1)


def field_angle(x, y):
    return noise.octaves(x * SCALE, y * SCALE, n=3) * math.pi * CURL


def hsl(h, s, l):
    return f"hsl({h % 360:.0f},{s:.0f}%,{l:.0f}%)"


def trace(x, y):
    """Walk one particle; return its polyline and mean heading."""
    pts = [(x, y)]
    sx = sy = 0.0
    for _ in range(STEPS):
        a = field_angle(x, y)
        sx += math.cos(a)
        sy += math.sin(a)
        x += STEP * math.cos(a)
        y += STEP * math.sin(a)
        if not (-50 <= x <= W + 50 and -50 <= y <= H + 50):
            break
        pts.append((x, y))
    return pts, math.atan2(sy, sx)


# ---------------------------------------------------------------- render

trails = []   # (pts, hue_deg, light_pct, width, opacity)
for _ in range(N_PARTICLES):
    pts, heading = trace(rng.uniform(0, W), rng.uniform(0, H))
    if len(pts) < 8:
        continue
    # palette: deep teal -> violet -> ember, keyed to heading
    t = (heading + math.pi) / (2 * math.pi)          # 0..1
    hue = 185 + 175 * t                              # 185..360
    light = 38 + 34 * abs(math.sin(heading * 2))
    width = 0.6 + 1.6 * rng.random() ** 2
    opacity = 0.16 + 0.22 * rng.random()
    trails.append((pts, hue, light, width, opacity))

paths = []
for pts, hue, light, width, opacity in trails:
    d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    paths.append(
        f'<path d="{d}" stroke="{hsl(hue, 72, light)}" '
        f'stroke-width="{width:.2f}" stroke-opacity="{opacity:.2f}" '
        f'fill="none" stroke-linecap="round"/>'
    )

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">\n'
    f'<rect width="{W}" height="{H}" fill="#0b0e14"/>\n'
    + "\n".join(paths)
    + "\n</svg>\n"
)

with open("flowfield.svg", "w") as f:
    f.write(svg)

print(f"wrote flowfield.svg — {len(paths)} trails")

# ----------------------------------------------------- pure-python PNG

PW, PH = W // 2, H // 2          # render at half res to keep it quick
BG = (11, 14, 20)                # matches #0b0e14
buf = [c for _ in range(PW * PH) for c in BG]   # flat RGB float-ish ints
acc = [float(v) for v in buf]


def splat(x, y, r, g, b, alpha):
    """Bilinear splat of one sample with alpha-over blending."""
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                      (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        px, py = x0 + dx, y0 + dy
        if 0 <= px < PW and 0 <= py < PH:
            i = (py * PW + px) * 3
            a = alpha * w
            acc[i] += (r - acc[i]) * a
            acc[i + 1] += (g - acc[i + 1]) * a
            acc[i + 2] += (b - acc[i + 2]) * a


for pts, hue, light, width, opacity in trails:
    r, g, b = (255 * c for c in colorsys.hls_to_rgb(
        (hue % 360) / 360, light / 100, 0.72))
    a = min(1.0, opacity * (0.7 + width * 0.5))
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        x1, y1, x2, y2 = x1 / 2, y1 / 2, x2 / 2, y2 / 2
        seg = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(seg / 0.7))
        for k in range(n):
            t = k / n
            splat(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r, g, b, a)


def png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data)))


raw = bytearray()
for row in range(PH):
    raw.append(0)  # filter: none
    i = row * PW * 3
    raw.extend(min(255, max(0, int(v))) for v in acc[i:i + PW * 3])

png = (b"\x89PNG\r\n\x1a\n"
       + png_chunk(b"IHDR", struct.pack(">IIBBBBB", PW, PH, 8, 2, 0, 0, 0))
       + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
       + png_chunk(b"IEND", b""))

with open("flowfield.png", "wb") as f:
    f.write(png)

print(f"wrote flowfield.png — {PW}x{PH}")

# ------------------------------------------------------- terminal preview

CW, CH = 100, 32
RAMP = " .:-=+*#%@"
cells = [[0.0] * CW for _ in range(CH)]
for p in range(1400):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    for _ in range(60):
        a = field_angle(x, y)
        x += STEP * math.cos(a)
        y += STEP * math.sin(a)
        cx, cy = int(x / W * CW), int(y / H * CH)
        if 0 <= cx < CW and 0 <= cy < CH:
            cells[cy][cx] += 1
peak = max(max(r) for r in cells) or 1
print("\npreview (trail density):")
for row in cells:
    print("".join(RAMP[min(int(v / peak * (len(RAMP) - 1) * 2.2),
                           len(RAMP) - 1)] for v in row))
