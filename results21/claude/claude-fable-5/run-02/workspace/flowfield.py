"""Flow field generative art -> SVG.

Thousands of particles trace paths through a smooth pseudo-noise vector
field. Stroke color follows the field angle; width tapers with path age.
Deterministic for a given seed.
"""

import math
import random

W, H = 1200, 800
SEED = 20260905
MARGIN = 60

rng = random.Random(SEED)

# --- smooth 2D value noise (bilinear-interpolated random grid, 3 octaves) ---
GRID = 8
grid = [[rng.random() * 2 * math.pi for _ in range(GRID + 2)] for _ in range(GRID + 2)]


def smooth(t):
    return t * t * (3 - 2 * t)


def noise(x, y):
    """Field angle at normalized coords (0..1), several octaves deep."""
    angle = 0.0
    amp, freq = 1.0, 1.0
    for _ in range(3):
        gx, gy = x * GRID * freq, y * GRID * freq
        ix, iy = int(gx) % GRID, int(gy) % GRID
        fx, fy = smooth(gx - int(gx)), smooth(gy - int(gy))
        a = grid[iy][ix]
        b = grid[iy][ix + 1]
        c = grid[iy + 1][ix]
        d = grid[iy + 1][ix + 1]
        top = a + (b - a) * fx
        bot = c + (d - c) * fx
        angle += (top + (bot - top) * fy) * amp
        amp *= 0.5
        freq *= 2.1
    return angle


# --- palette: deep ink background, strokes shift teal -> gold by angle ---
def lerp(a, b, t):
    return a + (b - a) * t


def color_for(angle):
    t = (math.sin(angle) + 1) / 2
    # teal (36,140,141) -> sand gold (222,170,90), with a violet accent band
    if 0.42 < t < 0.50:
        return "#8a6fb3"
    r = int(lerp(36, 222, t))
    g = int(lerp(140, 170, t))
    b = int(lerp(141, 90, t))
    return f"#{r:02x}{g:02x}{b:02x}"


strokes = []  # (pts, color, width, opacity)
N_PARTICLES = 2600
STEP = 3.2
MAX_STEPS = 90

for _ in range(N_PARTICLES):
    x = rng.uniform(MARGIN, W - MARGIN)
    y = rng.uniform(MARGIN, H - MARGIN)
    pts = [(x, y)]
    a0 = noise(x / W, y / H)
    for _ in range(rng.randint(20, MAX_STEPS)):
        a = noise(x / W, y / H)
        x += math.cos(a) * STEP
        y += math.sin(a) * STEP
        if not (0 < x < W and 0 < y < H):
            break
        pts.append((x, y))
    if len(pts) < 6:
        continue
    width = 0.6 + 1.6 * (len(pts) / MAX_STEPS)
    opacity = 0.28 + 0.5 * rng.random()
    strokes.append((pts, color_for(a0), width, opacity))

svg_paths = []
for pts, color, width, opacity in strokes:
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    svg_paths.append(
        f'<path d="{d}" stroke="{color}" stroke-width="{width:.2f}" '
        f'stroke-opacity="{opacity:.2f}" fill="none" stroke-linecap="round"/>'
    )

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">\n'
    f'<rect width="{W}" height="{H}" fill="#101418"/>\n'
    + "\n".join(svg_paths)
    + "\n</svg>\n"
)

with open("/workspace/flowfield.svg", "w") as f:
    f.write(svg)

print(f"wrote flowfield.svg: {len(strokes)} strokes, seed {SEED}")

# --- optional PNG render (supersampled 2x) if Pillow is available ---
try:
    from PIL import Image, ImageDraw
except ImportError:
    pass
else:
    S = 2
    img = Image.new("RGB", (W * S, H * S), "#101418")
    draw = ImageDraw.Draw(img, "RGBA")
    for pts, color, width, opacity in strokes:
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        rgba = rgb + (int(opacity * 255),)
        scaled = [(px * S, py * S) for px, py in pts]
        draw.line(scaled, fill=rgba, width=max(1, round(width * S)), joint="curve")
    img = img.resize((W, H), Image.LANCZOS)
    img.save("/workspace/flowfield.png")
    print("wrote flowfield.png")
