# reaction-diffusion

A Gray-Scott reaction-diffusion simulation in a single C file with no
dependencies. It writes a PNG directly, including its own CRC-32, Adler-32,
and stored-block deflate stream, so it needs neither zlib nor libpng.

## Build and run

```sh
cc -O2 -o rd rd.c -lm
./rd coral 10000 coral.png
```

Arguments are `preset`, `steps`, and `output` in that order. All are optional.

## Presets

| name    | feed F | kill k | what you get                              |
|---------|--------|--------|-------------------------------------------|
| coral   | 0.0545 | 0.0620 | labyrinthine stripes                      |
| mitosis | 0.0367 | 0.0649 | spots that split like dividing cells      |
| maze    | 0.0290 | 0.0570 | branching, maze-like channels             |
| worms   | 0.0580 | 0.0650 | short wriggling segments                  |
| spots   | 0.0300 | 0.0620 | isolated dots                             |

## How it works

Two chemicals U and V live on a 512 x 512 toroidal grid. U is fed in at
rate F, V is removed at rate F + k, and the reaction U + 2V -> 3V converts
one into the other. Diffusion uses a 9-point Laplacian with Du = 1.0 and
Dv = 0.5 and a time step of 1. The image maps the square root of V through a
navy, teal, amber, cream colour ramp.

The PNG writer packs the raw scanlines into uncompressed deflate blocks of
65535 bytes each, so files are about 787 KB regardless of content.
