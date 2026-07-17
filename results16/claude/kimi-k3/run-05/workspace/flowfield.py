#!/usr/bin/env python3
"""Flow field generative art — pure stdlib Python.

Thousands of particles drift along a curl-noise-ish vector field built from
seeded sine octaves, depositing light onto an additive HDR buffer with
deterministic subpixel jitter. Then: tonemap, palette, gamma, PNG.

Usage: python3 flowfield.py [seed]
"""

import math
import random
import struct
import sys
import zlib

W, H = 1440, 900


# ---------------------------------------------------------------- png writer

def write_png(path, width, height, rgb_rows):
    """rgb_rows: iterable of bytearrays of length width*3 (8-bit RGB)."""
    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)  # filter: none
        raw.extend(row)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ------------------------------------------------------------ vector field

class Field:
    """Angle field from summed incommensurate sines; smoothly warped by seed."""

    def __init__(self, rng):
        self.octaves = []
        for i in range(4):
            self.octaves.append((
                rng.uniform(0.5, 1.4) * (1.7 ** i),   # x frequency
                rng.uniform(0.5, 1.4) * (1.7 ** i),   # y frequency
                rng.uniform(0, math.tau),             # phase 1
                rng.uniform(0, math.tau),             # phase 2
                rng.uniform(-1, 1),                   # x/y coupling
                1.0 / (1.9 ** i),                     # amplitude falloff
            ))
        self.scale = rng.uniform(2.2, 3.1)
        self.twist = rng.uniform(-0.9, 0.9)           # global swirl

    def angle(self, x, y):
        # x, y in roughly [-1, 1]
        v = 0.0
        for fx, fy, p1, p2, c, amp in self.octaves:
            v += amp * math.sin(fx * (x + c * y) * math.pi + p1)
            v += amp * math.cos(fy * (y - c * x) * math.pi + p2)
        r2 = x * x + y * y
        v += self.twist * r2 * 2.0
        return v * self.scale


# ------------------------------------------------------------------ render

def lerp(a, b, t):
    return a + (b - a) * t


def make_palettes(rng):
    """Palette as cosine gradient: c(t) = a + b*cos(tau*(c*t + d))."""
    def cos_grad():
        return ([rng.uniform(0.25, 0.75) for _ in range(3)],
                [rng.uniform(0.15, 0.45) for _ in range(3)],
                [rng.uniform(0.6, 1.1) for _ in range(3)],
                [rng.uniform(0, 1) for _ in range(3)])

    def pal(t):
        a, b, c, d = grad
        return [a[i] + b[i] * math.cos(math.tau * (c[i] * t + d[i])) for i in range(3)]

    grad = cos_grad()
    # force a moody dark start and a luminous end regardless of random draws
    start = [rng.uniform(0.02, 0.10) for _ in range(3)]
    end = sorted([rng.uniform(0.75, 1.0) for _ in range(3)], reverse=True)
    return start, pal, end


def render(seed):
    rng = random.Random(seed)
    field = Field(rng)
    start_col, mid_pal, end_col = make_palettes(rng)

    n_particles = 6500
    steps = 260
    step_len = 0.0016 * max(W, H) / 1440.0 * 2.2

    acc = [0.0] * (W * H * 3)

    cx, cy = W * 0.5, H * 0.5
    norm = 2.4 / max(W, H)

    for p in range(n_particles):
        # biased spawn: mix of uniform and gaussian clumps
        if rng.random() < 0.55:
            x = rng.uniform(0, W)
            y = rng.uniform(0, H)
        else:
            gx, gy = rng.uniform(0.25, 0.75) * W, rng.uniform(0.25, 0.75) * H
            spread = rng.uniform(0.08, 0.30) * W
            x = rng.gauss(gx, spread)
            y = rng.gauss(gy, spread * 0.75)

        t_base = rng.random()
        hue_speed = rng.uniform(0.25, 0.9)
        life = int(steps * rng.uniform(0.45, 1.0))
        bright = rng.uniform(0.35, 1.0)

        for s in range(life):
            fx = (x - cx) * norm
            fy = (y - cy) * norm
            a = field.angle(fx, fy)
            x += math.cos(a) * step_len * 60 * 0.016
            y += math.sin(a) * step_len * 60 * 0.016

            # a few jittered subpixel samples per step -> continuous filaments
            t = min(1.0, t_base + hue_speed * s / steps)
            if t < 0.5:
                u = t * 2.0
                col = [lerp(start_col[i], mid_pal(u)[i], u) for i in range(3)]
            else:
                u = (t - 0.5) * 2.0
                col = [lerp(mid_pal(u)[i], end_col[i], u * u) for i in range(3)]
            gain = bright * (0.25 + 0.75 * s / life)  * 0.07
            gr, gg, gb = col[0] * gain, col[1] * gain, col[2] * gain
            for k in range(4):
                px = int(x + (rng.random() - 0.5) * 1.4)
                py = int(y + (rng.random() - 0.5) * 1.4)
                if 0 <= px < W and 0 <= py < H:
                    idx = (py * W + px) * 3
                    acc[idx] += gr
                    acc[idx + 1] += gg
                    acc[idx + 2] += gb

    # ------------------------------------------------- tonemap + palette out
    bg = [start_col[0] * 0.06, start_col[1] * 0.06, start_col[2] * 0.10 + 0.012]
    rows = []
    inv_gamma = 1.0 / 2.2
    soft = 1.7  # filmic-ish shoulder
    for y in range(H):
        row = bytearray(W * 3)
        base = y * W * 3
        for x in range(W):
            i = base + x * 3
            r = acc[i] + bg[0]
            g = acc[i + 1] + bg[1]
            b = acc[i + 2] + bg[2]
            # Reinhard with soft shoulder, then gamma
            r = (r / (1 + r)) ** inv_gamma * soft
            g = (g / (1 + g)) ** inv_gamma * soft
            b = (b / (1 + b)) ** inv_gamma * soft
            row[x * 3] = 255 if r > 1 else int(r * 255)
            row[x * 3 + 1] = 255 if g > 1 else int(g * 255)
            row[x * 3 + 2] = 255 if b > 1 else int(b * 255)
        rows.append(row)
    return rows


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 17
    out = sys.argv[2] if len(sys.argv) > 2 else f"flow_{seed}.png"
    print(f"seed={seed} rendering {W}x{H} ...", flush=True)
    rows = render(seed)
    write_png(out, W, H, rows)
    print(f"wrote {out}")
