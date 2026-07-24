# turing — Gray–Scott reaction–diffusion in pure Python

Two chemicals, one autocatalytic reaction, and a dish that leaks. Alan Turing's
1952 argument was that this is enough: diffusion alone can *break* symmetry
rather than smooth it out, so a featureless dish spontaneously grows spots and
stripes. This renders that, in the terminal, with no dependencies — not even
numpy.

```
du/dt = Du·∇²u − u·v² + F·(1 − u)
dv/dt = Dv·∇²v + u·v² − (F + k)·v
```

`F` is the feed rate, `k` the kill rate. Almost every interesting behaviour
lives in a thin sliver of the (F, k) plane; step outside it and the dish
relaxes to a uniform, boring fixed point.

## Use

```bash
python3 -m turing --preset labyrinth              # print a pattern
python3 -m turing --preset coral --steps 20000 --ppm coral.ppm
python3 -m unittest discover -s turing -t .       # 11 tests
```

Presets: `spots`, `mitosis`, `labyrinth`, `coral`, `worms`, `bubbles`, `solitons`.

## What it looks like

`labyrinth` (F=0.029, k=0.057) — ridges that grow until they run out of room,
the same space-filling process as a fingerprint:

```
 .:-=+*###%%%%%%#*=-:....:-=+**###%%%*=:.   .:-=++=-:....-=+*###***++=
.::-==+*###%%%%##****##%%%##*=-::......:=+##%%%##**+++==-:..   .:=*%%@@%*=:
=+*###%%%%%##*+=------=*##%%%##*+=-:....:-+*%%%##*+=-:.........:-=*#####+=:
%%%###***++=-::...  ...:-=*##%%%%#*++=--::--=+##%#*+-::.....::--==++***#**+-
```

`mitosis` (F=0.0367, k=0.0649) — spots that grow, pinch in the middle, and
divide, then jostle their neighbours into a lattice:

```
%@@@%*-.  .:=*##*+:.     ....    .:+#@@@%+:.      .      .:---:..
=*#*+-.. ..-*%@@@#=:.  .:-===-..  .:=+*+=:.             .-*#%%#+-.
..:...    .-*%@@%*-....-+%@@%#=:.   .....    ..::...   .:=#@@@@#=:.
```

`coral` (F=0.055, k=0.062) grows by tip-splitting; `solitons` (F=0.014,
k=0.054) produces self-sustaining travelling waves that leave wakes and
annihilate on collision.

## How it goes fast without numpy

The naive version indexes four neighbours per cell in a Python loop. Instead,
each Laplacian is assembled from whole-list slices — one C-level copy per
shift — and the timestep is two list comprehensions over `zip`. That runs at
**~3.6M cell-updates/second** on one core, about 30× the nested-loop version,
and it's less code.

One subtlety: the vertical shifts are plain slices of the flat row-major list,
but the horizontal ones must be done per row. Shifting the flat list by one
would wrap row *r*'s left edge onto row *r−1*'s right edge — stitching the
torus into a helix and leaving a diagonal seam through the pattern.
`test_horizontal_wrap_stays_within_its_row` pins this down.

## Notes on the physics, learned the hard way

The uniform state u=1, v=0 is an *exact* fixed point, so the dish must be
perturbed to do anything. But over-seeding kills it just as dead: a field that
is locally uniform has zero Laplacian there, so a grid blotted edge-to-edge
with V relaxes straight back to flat. The initial patch count therefore scales
with grid area rather than being a fixed number — a bug the test suite caught
on a 32×32 grid, where 24 patches covered everything twice over.

Terminal characters are about twice as tall as they are wide, so the simulation
runs at 2× vertical resolution and the renderer averages row pairs. Without
that, every circular spot renders as an ellipse.

`--ppm` writes a binary P6 image (viewable directly, or `pnmtopng`), coloured
on a deep-indigo → teal → cream ramp.
