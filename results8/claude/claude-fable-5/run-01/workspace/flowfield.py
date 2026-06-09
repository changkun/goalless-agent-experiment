"""Flow field — generative art in pure Python stdlib.

Thousands of particles drift through a fractal value-noise vector field,
leaving additive ink trails. The result is written out as a PNG by hand
(zlib-compressed scanlines, no imaging libraries).

Run:  python3 flowfield.py [seed]
"""

import math
import random
import struct
import sys
import zlib

W, H = 1280, 800
PARTICLES = 14000
STEPS = 220
STEP_LEN = 1.6
NOISE_SCALE = 0.0022
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7


# ----- value noise with fBm ------------------------------------------------

class Noise:
    def __init__(self, seed):
        rng = random.Random(seed)
        self.perm = list(range(256))
        rng.shuffle(self.perm)
        self.perm += self.perm
        self.vals = [rng.random() for _ in range(256)]

    def _lattice(self, ix, iy):
        return self.vals[self.perm[(self.perm[ix & 255] + iy) & 255]]

    def at(self, x, y):
        ix, iy = math.floor(x), math.floor(y)
        fx, fy = x - ix, y - iy
        # smoothstep fade
        ux = fx * fx * (3 - 2 * fx)
        uy = fy * fy * (3 - 2 * fy)
        a = self._lattice(ix, iy)
        b = self._lattice(ix + 1, iy)
        c = self._lattice(ix, iy + 1)
        d = self._lattice(ix + 1, iy + 1)
        return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy

    def fbm(self, x, y, octaves=4):
        total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
        for _ in range(octaves):
            total += amp * self.at(x * freq, y * freq)
            norm += amp
            amp *= 0.5
            freq *= 2.0
        return total / norm


# ----- palette --------------------------------------------------------------

def lerp(a, b, t):
    return a + (b - a) * t

# deep-sea gradient: ink blue -> teal -> gold -> ember
PALETTE = [
    (0.10, 0.22, 0.40),
    (0.05, 0.55, 0.55),
    (0.95, 0.75, 0.25),
    (0.90, 0.35, 0.20),
]

def palette(t):
    t = max(0.0, min(0.9999, t)) * (len(PALETTE) - 1)
    i = int(t)
    f = t - i
    c0, c1 = PALETTE[i], PALETTE[i + 1]
    return (lerp(c0[0], c1[0], f), lerp(c0[1], c1[1], f), lerp(c0[2], c1[2], f))


# ----- render ---------------------------------------------------------------

def render():
    noise = Noise(SEED)
    rng = random.Random(SEED * 31 + 1)

    # float accumulation buffer, dark blue-black base
    base = (0.020, 0.025, 0.045)
    buf = [c for _ in range(W * H) for c in base]

    alpha = 0.085
    for p in range(PARTICLES):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        # color keyed to the noise value at the spawn point
        t = noise.fbm(x * NOISE_SCALE * 1.7 + 40.0, y * NOISE_SCALE * 1.7 + 40.0)
        r, g, b = palette(t * 1.35 - 0.15)

        for s in range(STEPS):
            n = noise.fbm(x * NOISE_SCALE, y * NOISE_SCALE)
            ang = n * math.tau * 2.0  # wraps twice -> swirls
            x += math.cos(ang) * STEP_LEN
            y += math.sin(ang) * STEP_LEN
            if not (0 <= x < W and 0 <= y < H):
                break
            # fade the tail slightly toward the end of the trail
            k = alpha * (1.0 - 0.5 * s / STEPS)
            i = (int(y) * W + int(x)) * 3
            buf[i] += r * k
            buf[i + 1] += g * k
            buf[i + 2] += b * k

        if p % 500 == 0:
            print(f"  particles: {p}/{PARTICLES}", flush=True)

    # tone map (soft knee) and gamma, then quantize
    out = bytearray(W * H * 3)
    inv_gamma = 1 / 2.2
    for i, v in enumerate(buf):
        v = v / (1.0 + v * 0.55)        # compress highlights
        v = v ** inv_gamma
        out[i] = min(255, int(v * 255 + 0.5))
    return out


# ----- minimal PNG writer ---------------------------------------------------

def write_png(path, pixels):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += pixels[yy * stride:(yy + 1) * stride]

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    print(f"rendering {W}x{H}, seed={SEED} ...")
    px = render()
    out = f"flowfield_{SEED}.png"
    write_png(out, px)
    print(f"wrote {out}")
