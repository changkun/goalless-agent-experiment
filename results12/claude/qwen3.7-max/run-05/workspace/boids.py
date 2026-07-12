"""Boids flocking simulation with SVG snapshot.

Classic Reynolds rules: separation, alignment, cohesion. Runs a few hundred
steps, then writes an SVG of the final frame. Pass --animate to watch in the
terminal (clears screen each frame).
"""
from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

W, H = 800, 600
N = 120
MAX_SPEED = 3.0
NEIGHBOR_R = 50.0
SEP_R = 18.0
W_SEP, W_ALI, W_COH = 1.6, 1.0, 0.9


@dataclass
class Boid:
    x: float
    y: float
    vx: float
    vy: float


def step(boids: list[Boid]) -> None:
    nr2, sr2 = NEIGHBOR_R * NEIGHBOR_R, SEP_R * SEP_R
    for b in boids:
        sx = sy = ax = ay = cx = cy = 0.0
        sn = an = cn = 0
        for o in boids:
            if o is b:
                continue
            dx, dy = o.x - b.x, o.y - b.y
            d2 = dx * dx + dy * dy
            if d2 < sr2 and d2 > 0:
                d = math.sqrt(d2)
                sx -= dx / d
                sy -= dy / d
                sn += 1
            if d2 < nr2:
                ax += o.vx; ay += o.vy; an += 1
                cx += o.x;  cy += o.y;  cn += 1
        fx = fy = 0.0
        if sn: fx += sx / sn * W_SEP; fy += sy / sn * W_SEP
        if an:
            ax /= an; ay /= an
            fx += (ax - b.vx) * W_ALI * 0.1
            fy += (ay - b.vy) * W_ALI * 0.1
        if cn:
            cx /= cn; cy /= cn
            fx += (cx - b.x) * W_COH * 0.005
            fy += (cy - b.y) * W_COH * 0.005
        b.vx += fx; b.vy += fy
        sp = math.hypot(b.vx, b.vy)
        if sp > MAX_SPEED:
            b.vx = b.vx / sp * MAX_SPEED
            b.vy = b.vy / sp * MAX_SPEED
        b.x = (b.x + b.vx) % W
        b.y = (b.y + b.vy) % H


def render_svg(boids: list[Boid], path: str) -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="#0b1020"/>',
    ]
    for b in boids:
        a = math.atan2(b.vy, b.vx)
        r = 6
        pts = [
            (b.x + math.cos(a) * r,       b.y + math.sin(a) * r),
            (b.x + math.cos(a + 2.4) * r, b.y + math.sin(a + 2.4) * r),
            (b.x + math.cos(a - 2.4) * r, b.y + math.sin(a - 2.4) * r),
        ]
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        parts.append(f'<polygon points="{s}" fill="#7cd3ff" opacity="0.85"/>')
    parts.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(parts))


def render_term(boids: list[Boid]) -> str:
    tw, th = 80, 30
    grid = [[" " for _ in range(tw)] for _ in range(th)]
    for b in boids:
        tx = int(b.x / W * (tw - 1))
        ty = int(b.y / H * (th - 1))
        a = math.atan2(b.vy, b.vx)
        ch = "><^v"[int((a / math.pi + 1) * 2) % 4]
        grid[ty][tx] = ch
    return "\n".join("".join(row) for row in grid)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--animate", action="store_true")
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--out", default="boids.svg")
    args = ap.parse_args()

    boids = [
        Boid(random.random() * W, random.random() * H,
             random.uniform(-1, 1), random.uniform(-1, 1))
        for _ in range(N)
    ]

    if args.animate:
        import os, time
        for i in range(args.steps):
            step(boids)
            print(f"\033[H\033[2Jframe {i+1}/{args.steps}")
            print(render_term(boids))
            time.sleep(0.033)
    else:
        for _ in range(args.steps):
            step(boids)

    render_svg(boids, args.out)
    if not args.animate:
        print(f"Wrote {args.out} ({N} boids, {args.steps} steps)")


if __name__ == "__main__":
    main()
