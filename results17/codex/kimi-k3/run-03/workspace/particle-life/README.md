# Particle Life

A tiny, dependency-free artificial-life toy. Colored particle species
attract or repel each other through a simple distance-based force law —
and surprisingly lifelike behavior falls out: pulsing cells, orbiting
clusters, predators chasing prey, shimmering swarms.

Everything (positions, the force matrix "genome", species colors) derives
from a single text **seed**, so any universe you like can be shared and
revisited exactly.

## Run it

No build step, no dependencies. Either open `index.html` directly, or
serve the folder:

```sh
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Controls

| Control        | What it does                                              |
| -------------- | --------------------------------------------------------- |
| Seed           | Text seed; `Load` rebuilds the universe, `⚀` randomizes  |
| Particles      | Population size (200–4000)                                |
| Species        | Number of colors (2–7); rerolls the force matrix          |
| Radius         | How far particles sense each other                        |
| Force strength | Global attraction/repulsion multiplier                    |
| Friction       | Velocity damping — low values get wild, high ones gummy   |
| Burst          | Kicks kinetic energy into a stale universe                |
| Speed          | Simulation time scale                                     |

Keyboard: `Space` pause/play · `B` burst · `H` hide/show panel.

## Sharing a universe

The seed is mirrored into the URL (`?seed=...`), so copy the address bar
to share the exact same universe with someone else.

## How it works

- Each ordered species pair gets a random affinity in `[-1, 1]` — an
  asymmetric matrix that acts as the universe's genome.
- Each tick, particles feel close-range repulsion plus mid-range
  attraction/repulsion from neighbors within the interaction radius.
- A spatial hash grid keeps neighbor lookup ~O(n), so a few thousand
  particles run smoothly in a plain `<canvas>` 2D context.
- The world is toroidal: particles wrap around the edges.
