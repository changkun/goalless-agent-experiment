# Flow Field

Generative art in pure Python stdlib — no dependencies, not even an imaging
library (the PNG encoder is ~15 lines of zlib + struct).

14,000 particles drift through a fractal value-noise vector field, each leaving
an additive ink trail. Where streamlines converge, the accumulated light forms
bright ridges; a soft-knee tone map and gamma curve keep the highlights from
clipping. Colors come from a deep-sea palette (ink blue → teal → gold → ember)
keyed to the noise value at each particle's spawn point.

## Run

```sh
python3 flowfield.py [seed]
```

Renders a 1280×800 PNG (`flowfield_<seed>.png`) in a couple of seconds.
Every seed is a different piece — `7`, `23`, and `101` are included.

## Knobs worth turning

- `NOISE_SCALE` — zoom level of the field (smaller = broader currents)
- `ang = n * math.tau * 2.0` — the `2.0` is swirl intensity; higher wraps the
  angle more times and produces tighter vortices
- `PALETTE` — four RGB stops, interpolated linearly
- `PARTICLES` / `STEPS` / `alpha` — ink density
