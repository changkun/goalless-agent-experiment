# flowfield

Generative art from a noise-driven flow field — pure Python, **zero dependencies**.

A swarm of particles is dropped onto a 2D [Perlin noise](https://en.wikipedia.org/wiki/Perlin_noise)
field. Each particle reads the noise value at its position, turns that into an
angle, and steps forward — over and over. The accumulated trails form smooth,
organic streamlines that all bend in harmony with the underlying field.

Everything is implemented from scratch in the standard library:
- **`flowfield.py`** — gradient (Perlin) noise + flow tracing → **SVG** (vector).
- **`render_png.py`** — the same field rasterised with additive blending → **PNG**,
  using a hand-rolled PNG encoder (`zlib` only). Overlapping trails build up
  light, so ridges in the field glow.

## Usage

```bash
python3 flowfield.py  --palette ember  --seed 7 --out art.svg
python3 render_png.py --palette lagoon --seed 7 --out art.png
```

Options: `--seed`, `--palette {ember,lagoon,orchid,mono}`, `--width`, `--height`, `--out`.

Change the `--seed` for a completely different composition; change `--palette`
to recolour the same field.
