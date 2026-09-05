# flowfield

Tiny zero-dependency generative art. Particles drift through a 2D value-noise
flow field; their paths become the artwork.

```
python3 flowfield.py [seed]        # -> flowfield_<seed>.svg
python3 rasterize.py <seed> [out]  # -> same artwork as a PNG (pure-Python rasterizer)
```

Same seed = same artwork in both formats (the two scripts consume the RNG
stream identically). Five palettes: dusk, tide, ember, moss, orchid — chosen
by the seed.

How it works, in three sentences: `make_noise` builds smooth 2D value noise
from a random lattice with cosine interpolation. Each of ~420 particles reads
the noise at its position, converts it to a heading, and steps 2.4 px in that
direction for up to 140 steps. Because the field is static, nearby particles
converge into shared "rivers", which is what gives the images their braided,
wind-swept look.
