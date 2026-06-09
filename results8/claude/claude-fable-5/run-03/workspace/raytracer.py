#!/usr/bin/env python3
"""A tiny ray tracer in pure Python — no dependencies.

Renders three reflective spheres on a checkerboard plane under a sky
gradient, with soft shadows from an area light, and writes a PPM image.
"""
import math
import random

W, H = 640, 360
MAX_DEPTH = 4
SHADOW_SAMPLES = 8
random.seed(42)

# --- minimal vector ops on 3-tuples -------------------------------------
def add(a, b):  return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def sub(a, b):  return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def mul(a, s):  return (a[0]*s, a[1]*s, a[2]*s)
def hada(a, b): return (a[0]*b[0], a[1]*b[1], a[2]*b[2])
def dot(a, b):  return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def norm(a):
    l = math.sqrt(dot(a, a))
    return (a[0]/l, a[1]/l, a[2]/l)
def reflect(d, n):
    return sub(d, mul(n, 2.0 * dot(d, n)))

# --- scene ----------------------------------------------------------------
# sphere: (center, radius, color, reflectivity, specular_power)
SPHERES = [
    ((0.0,  1.0,  3.5), 1.0, (0.90, 0.25, 0.20), 0.20, 200),  # red
    ((-2.1, 0.7,  4.5), 0.7, (0.20, 0.45, 0.95), 0.15, 120),  # blue
    (( 1.9, 0.6,  2.4), 0.6, (0.95, 0.85, 0.30), 0.30, 300),  # gold
]
LIGHT_POS = (-4.0, 6.0, 0.0)
LIGHT_RADIUS = 0.8
LIGHT_COLOR = (1.0, 0.97, 0.92)
AMBIENT = 0.08
CAM = (0.0, 1.2, -2.5)

def sky(d):
    t = 0.5 * (d[1] + 1.0)
    horizon = (0.95, 0.85, 0.70)
    zenith = (0.35, 0.55, 0.90)
    return add(mul(horizon, 1.0 - t), mul(zenith, t))

def checker(p):
    if (math.floor(p[0]) + math.floor(p[2])) % 2 == 0:
        return (0.85, 0.85, 0.85)
    return (0.18, 0.18, 0.22)

def hit_sphere(orig, d, center, radius):
    oc = sub(orig, center)
    b = dot(oc, d)
    c = dot(oc, oc) - radius * radius
    disc = b * b - c
    if disc < 0:
        return None
    s = math.sqrt(disc)
    for t in (-b - s, -b + s):
        if t > 1e-4:
            return t
    return None

def intersect(orig, d):
    """Returns (t, point, normal, color, reflectivity, spec_power) or None."""
    best = None
    for center, radius, color, refl, spec in SPHERES:
        t = hit_sphere(orig, d, center, radius)
        if t is not None and (best is None or t < best[0]):
            p = add(orig, mul(d, t))
            n = norm(sub(p, center))
            best = (t, p, n, color, refl, spec)
    # floor plane y = 0
    if abs(d[1]) > 1e-6:
        t = -orig[1] / d[1]
        if t > 1e-4 and (best is None or t < best[0]):
            p = add(orig, mul(d, t))
            best = (t, p, (0.0, 1.0, 0.0), checker(p), 0.15, 60)
    return best

def light_visibility(p):
    """Fraction of area-light samples visible from p (soft shadows)."""
    seen = 0
    for _ in range(SHADOW_SAMPLES):
        jitter = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
        lp = add(LIGHT_POS, mul(jitter, LIGHT_RADIUS))
        to_l = sub(lp, p)
        dist = math.sqrt(dot(to_l, to_l))
        d = mul(to_l, 1.0 / dist)
        hit = intersect(p, d)
        if hit is None or hit[0] > dist:
            seen += 1
    return seen / SHADOW_SAMPLES

def trace(orig, d, depth):
    hit = intersect(orig, d)
    if hit is None:
        return sky(d)
    _, p, n, color, refl, spec = hit

    to_l = norm(sub(LIGHT_POS, p))
    vis = light_visibility(p)
    diff = max(0.0, dot(n, to_l)) * vis

    # Blinn-Phong specular
    half = norm(sub(to_l, d))
    spec_i = (max(0.0, dot(n, half)) ** spec) * vis

    col = add(mul(hada(color, LIGHT_COLOR), AMBIENT + 1.1 * diff),
              mul(LIGHT_COLOR, 0.6 * spec_i))

    if depth < MAX_DEPTH and refl > 0:
        # Schlick's Fresnel: base reflectivity head-on, ramping to 1 at grazing
        cos_i = max(0.0, -dot(d, n))
        fr = refl + (1.0 - refl) * (1.0 - cos_i) ** 5
        rd = norm(reflect(d, n))
        rcol = trace(add(p, mul(n, 1e-4)), rd, depth + 1)
        col = add(mul(col, 1.0 - fr), mul(rcol, fr))
    return col

def render():
    aspect = W / H
    fov_scale = math.tan(math.radians(55) / 2)
    rows = []
    for y in range(H):
        row = bytearray()
        for x in range(W):
            # 2x2 supersampling
            c = (0.0, 0.0, 0.0)
            for sx in (0.25, 0.75):
                for sy in (0.25, 0.75):
                    u = (2 * (x + sx) / W - 1) * aspect * fov_scale
                    v = (1 - 2 * (y + sy) / H) * fov_scale
                    d = norm((u, v, 1.0))
                    c = add(c, trace(CAM, d, 0))
            c = mul(c, 0.25)
            for ch in c:
                # gamma 2.2
                row.append(min(255, int((max(0.0, ch) ** (1 / 2.2)) * 255)))
        rows.append(bytes(row))
        if y % 40 == 0:
            print(f"  row {y}/{H}")
    return rows

if __name__ == "__main__":
    rows = render()
    with open("render.ppm", "wb") as f:
        f.write(f"P6\n{W} {H}\n255\n".encode())
        for r in rows:
            f.write(r)
    print("wrote render.ppm")
