#!/usr/bin/env python3
"""
UMBRA — a sea of coupled pendulums, rendered in your terminal.

A grid of small rotations. Each pendulum swings at a natural frequency
shaped by concentric rings and obeys its own cosine restoring force —
and each tugs on its neighbors. The grid's edge pins the motion, so
the sea forms standing modes that swell, breathe, and drift. Nothing
is scripted: every frame is emergent.

    python3 umbra.py            # run the tide (ctrl-c to release)
    python3 umbra.py --frames 5 # render 5 plain frames and exit (for pipes)
"""

import math
import random
import shutil
import signal
import sys
import time

# ---------------------------------------------------------------- config

FPS = 24
DT = 0.05           # integration step
GAMMA = 0.012       # friction (low: the sea keeps breathing)
K = 0.60            # neighbor coupling strength
DRIVE_AMP = 2.6     # source injection strength
RAMP = " .:-=+*#%@"

# truecolor palette stops (phase -1..+1 -> deep sea -> aurora -> totality).
# The midpoint is genuine darkness, so calm water is a dark sea, not fog.
PALETTE = [
    (-1.00, (2, 6, 18)),
    (-0.55, (8, 22, 54)),
    (-0.15, (14, 50, 72)),
    (0.00, (5, 9, 20)),      # still water: dark
    (0.15, (16, 74, 84)),
    (0.45, (34, 138, 122)),
    (0.75, (120, 208, 168)),
    (1.00, (240, 255, 230)),
]

# ---------------------------------------------------------------- palette


def lerp_color(p):
    """Piecewise-linear interpolation through PALETTE. p in [-1,1]."""
    if p <= PALETTE[0][0]:
        return PALETTE[0][1]
    if p >= PALETTE[-1][0]:
        return PALETTE[-1][1]
    for i in range(len(PALETTE) - 1):
        t0, c0 = PALETTE[i]
        t1, c1 = PALETTE[i + 1]
        if t0 <= p <= t1:
            f = (p - t0) / (t1 - t0)
            return (
                int(c0[0] + (c1[0] - c0[0]) * f),
                int(c0[1] + (c1[1] - c0[1]) * f),
                int(c0[2] + (c1[2] - c0[2]) * f),
            )
    return PALETTE[-1][1]


# Precompute a lookup table indexed by phase + twinkle:
#   idx = int((p + 1) / 2 * 255)   for p = sin(theta) in [-1,1]
# and a second table shifted brighter for star cells at full twinkle.
LUT = []
LUT_STAR = []
for i in range(256):
    p = i / 255.0 * 2.0 - 1.0          # phase in [-1, 1]
    lum = max(0.0, p)                   # chars glow on the bright half-swing
    ch = RAMP[min(int(lum * len(RAMP)), len(RAMP) - 1)]
    r, g, b = lerp_color(p)
    LUT.append((ch, f"\x1b[38;2;{r};{g};{b}m"))
    ps = min(1.0, p + 0.30)             # star: nudged toward totality
    lums = min(1.0, lum + 0.30)
    chs = RAMP[min(int(lums * len(RAMP)), len(RAMP) - 1)]
    r, g, b = lerp_color(ps)
    LUT_STAR.append((chs, f"\x1b[38;2;{r};{g};{b}m"))

RESET = "\x1b[0m"

# ---------------------------------------------------------------- field


class Field:
    """A w x h grid of damped, diffusively-coupled pendulums.

    Boundary cells are pinned (theta = 0, never updated): the edge acts
    as a wall, so traveling waves reflect and the sea forms standing
    modes that breathe instead of a static equilibrium.
    """

    def __init__(self, w, h, seed=None):
        self.w, self.h = w, h
        rng = random.Random(seed)
        n = w * h
        cx, cy = w / 2.0, h / 2.0
        max_r = math.hypot(cx, cy)

        self.theta = [rng.uniform(-0.25, 0.25) for _ in range(n)]  # angle
        self.dtheta = [0.0] * n                                    # angular vel
        self.w2 = [0.0] * n                                        # omega^2
        self.neigh = [None] * n
        self.free = [True] * n  # False on the boundary ring (pinned)

        for y in range(h):
            for x in range(w):
                i = y * w + x
                r = math.hypot(x - cx, (y - cy) * 2.0) / max_r  # *2: aspect
                # concentric rings of natural frequency + gentle turbulence
                om = (
                    0.70
                    + 0.22 * math.sin(r * 6.0)
                    + 0.10 * math.sin(x * 0.31 + 1.7) * math.cos(y * 0.27)
                )
                self.w2[i] = om * om
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    self.free[i] = False
                    self.theta[i] = 0.0
                nb = []
                if x > 0:
                    nb.append(i - 1)
                if x < w - 1:
                    nb.append(i + 1)
                if y > 0:
                    nb.append(i - w)
                if y < h - 1:
                    nb.append(i + w)
                self.neigh[i] = nb

        # sparse fixed "stars" that twinkle on their own slow clock
        self.stars = {}
        for _ in range(int(n * 0.012)):
            i = rng.randrange(n)
            self.stars[i] = (rng.uniform(0, 2 * math.pi), rng.uniform(0.4, 1.1))

        # driving sources: wander the interior, swell and die, reseed elsewhere
        self.src_pos = [0] * 3
        self.src_phase = [0.0] * 3
        self.src_om = [0.0] * 3
        self.src_birth = [0.0] * 3
        self.src_life = [1.0] * 3
        self.rng = rng
        for s in range(3):
            self._reseed(s, 0.0)
        self.t = 0.0

    def _reseed(self, s, t):
        rng = self.rng
        x = rng.randrange(2, self.w - 2)
        y = rng.randrange(2, self.h - 2)
        self.src_pos[s] = y * self.w + x
        self.src_phase[s] = rng.uniform(0, 2 * math.pi)
        self.src_om[s] = rng.uniform(0.55, 0.95)
        self.src_birth[s] = t
        self.src_life[s] = rng.uniform(30, 60)

    def step(self):
        theta, dtheta, w2, neigh, free = (
            self.theta, self.dtheta, self.w2, self.neigh, self.free)
        sin = math.sin
        n = len(theta)
        t = self.t

        # envelope of each driving source (smoothly swells and dies)
        drive = [0.0, 0.0, 0.0]
        for s in range(3):
            age = (t - self.src_birth[s]) / self.src_life[s]
            if age >= 1.0:  # burst over: reseed elsewhere
                self._reseed(s, t)
                age = 0.0
            env = sin(math.pi * min(age, 1.0))
            drive[s] = DRIVE_AMP * env * env * sin(self.src_om[s] * t + self.src_phase[s])

        sp = self.src_pos
        new = [0.0] * n
        for i in range(n):
            if not free[i]:
                continue  # pinned boundary
            th = theta[i]
            s = 0.0
            for j in neigh[i]:
                s += theta[j]
            acc = (
                -w2[i] * sin(th)
                - GAMMA * dtheta[i]
                + K * (s - len(neigh[i]) * th)
            )
            new[i] = dtheta[i] + acc * DT
        # inject driving into the velocity of the source cells
        for s in range(3):
            new[sp[s]] += drive[s] * DT

        for i in range(n):
            if free[i]:
                theta[i] += new[i] * DT
        self.dtheta = new
        self.t += DT

    def render(self, color=True):
        """Return the frame as a string (no trailing newline)."""
        w, h = self.w, self.h
        theta = self.theta
        sin, cos = math.sin, math.cos
        star = self.stars
        t = self.t
        # per-cell LUT index from phase, and which cells are currently twinkling
        lut_idx = [0] * (w * h)
        twinkle = [False] * (w * h)
        for i in range(w * h):
            p = sin(theta[i])
            lut_idx[i] = int((p + 1.0) * 127.5)
            st = star.get(i)
            if st is not None:
                twinkle[i] = cos(st[0] + t * st[1]) > 0.3  # ~40% duty cycle
        rows = []
        for y in range(h):
            base = y * w
            if color:
                parts = []
                for x in range(w):
                    i = base + x
                    ch, fg = (LUT_STAR if twinkle[i] else LUT)[lut_idx[i]]
                    parts.append(fg + ch)
                rows.append("".join(parts) + RESET)
            else:
                row = []
                for x in range(w):
                    i = base + x
                    ch = (LUT_STAR if twinkle[i] else LUT)[lut_idx[i]][0]
                    row.append(ch)
                rows.append("".join(row))
        return "\n".join(rows)


# ---------------------------------------------------------------- shell


def pick_size():
    ts = shutil.get_terminal_size((100, 32))
    return max(40, min(ts.columns, 118)), max(16, min(ts.lines - 2, 44))


def title_card():
    lines = [
        "",
        "        U M B R A",
        "",
        "  a sea of coupled pendulums",
        "  thousands of swings · one tide",
        "",
        "  — ctrl-c to release —",
    ]
    pad = "\n" * max(0, (shutil.get_terminal_size((100, 32)).lines - len(lines)) // 2)
    sys.stdout.write(pad + "\n".join(lines) + "\n")
    sys.stdout.flush()


def main():
    frames_mode = None
    if "--frames" in sys.argv:
        frames_mode = int(sys.argv[sys.argv.index("--frames") + 1])

    interactive = sys.stdout.isatty() and frames_mode is None
    w, h = pick_size()
    field = Field(w, h, seed=None if interactive else 7)

    if frames_mode is not None:
        # plain, deterministic, pipe-friendly: no ANSI screen control, no color
        for _ in range(600):  # warm-up: let the first tide develop
            field.step()
        for f in range(frames_mode):
            print(field.render(color=False))
            print(f"  · t={field.t:7.2f} · frame {f + 1}/{frames_mode} ·")
            for _ in range(25):
                field.step()
        return

    # ---- interactive mode ----
    sys.stdout.write("\x1b[?1049h\x1b[?25l")  # alt screen, hide cursor

    def cleanup(*_):
        sys.stdout.write(RESET + "\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    title_card()
    time.sleep(2.2)

    frames, t0 = 0, time.monotonic()
    frame_dur = 1.0 / FPS
    try:
        while True:
            start = time.monotonic()
            nw, nh = pick_size()
            if (nw, nh) != (w, h):  # terminal resized: reseed the sea
                w, h = nw, nh
                field = Field(w, h)
            field.step()
            buf = "\x1b[H" + field.render(color=True)
            sys.stdout.write(buf)
            sys.stdout.flush()
            frames += 1
            elapsed = time.monotonic() - start
            if elapsed < frame_dur:
                time.sleep(frame_dur - elapsed)
    except KeyboardInterrupt:
        pass
    finally:
        dt = time.monotonic() - t0
        sys.stdout.write(RESET + "\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        print(f"the tide recedes. {frames} frames · {dt:.1f}s · {frames / max(dt, 1e-9):.1f} fps")


if __name__ == "__main__":
    main()
