# UMBRA

*a sea of coupled pendulums, rendered in your terminal*

A grid of a few thousand small rotations. Each pendulum swings at a
natural frequency shaped by concentric rings, obeys its own cosine
restoring force, and tugs on its four neighbors. The grid's edge pins
the motion, so traveling waves reflect and the sea forms standing
modes that **swell, breathe, and drift**. Three wandering sources pump
energy in; friction takes it out. Nothing is scripted — every frame is
emergent.

No dependencies. Python 3.8+. One file.

## Run it

```sh
python3 umbra.py
```

(ctrl-c releases the sea and restores your terminal.)

```sh
python3 umbra.py --frames 10   # plain deterministic frames, pipe-friendly
cat preview.ans                # a colored snapshot, if your terminal allows
```

## What you're seeing

- **Brightness is phase**, not magnitude: `b = 0.5 + 0.42·sin(θ)`.
  The midpoint of the palette is genuine darkness, so calm water is a
  dark sea — light only appears where the tide stands tall.
- **Three sources** wander the interior on 30–60 second lives, each
  swelling and dying on a smooth envelope, then reseeding elsewhere.
  When two overlap, their interference writes moiré across the water.
- **Stars**: ~1% of cells twinkle on their own slow clocks, briefly
  nudged toward totality-white.

## The math

```
θ̈ᵢ = −ωᵢ²·sin(θᵢ)  −  γ·θ̇ᵢ  +  K·Σⱼ∈n(i) (θⱼ − θᵢ)  +  drive
```

symplectic Euler, `dt = 0.05`, tuned (γ = 0.012, K = 0.60, drive = 2.6)
so the field stays bounded for hours while never settling down.

## Tuning

All the knobs live at the top of `umbra.py`: `FPS`, `DT`, `GAMMA`,
`K`, `DRIVE_AMP`, the `RAMP` glyphs, and the `PALETTE` stops — swap in
your own colors; the palette is interpolated per-frame in truecolor.
