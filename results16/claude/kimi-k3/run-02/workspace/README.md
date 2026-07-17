# particle life

A zero-dependency artificial-life sandbox in a single HTML file.
Six species of dots follow one 6×6 attract/repel rule matrix — and from
those 36 numbers emerge clumps, orbiting pairs, chasing hunters, and
slow-breathing colonies. Every "rules" roll is a new universe.

## Run it

Open `particle-life.html` in any browser. That's it.
(Or serve it: `python3 -m http.server` → http://localhost:8000/particle-life.html)

## Controls

| input | action |
|---|---|
| drag | paint particles |
| shift-drag | stir the soup |
| `space` | pause / resume |
| `r` | random rule matrix |
| `n` | reseed particles |
| `m` | toggle the matrix editor |
| `h` | toggle help |
| `+` / `-` | zoom |
| click / right-click a matrix cell | nudge that rule ±0.25 |

**balanced** generates a near-antisymmetric matrix (A→B ≈ −(B→A)),
which reliably produces living worlds. **rules** rolls raw dice —
most universes die instantly; the interesting ones are why you keep clicking.

## How it works

- Pairwise force within radius `r`: hard-core repulsion inside `0.28r`,
  otherwise a triangular attraction profile peaking at `r/2`, scaled by
  the matrix entry `A[species_i][species_j]`.
- Uniform-grid spatial hash rebuilt each frame → ~O(n) instead of O(n²).
- SoA `Float32Array` storage, one batched canvas path per species.
- Toroidal world (edges wrap).

Tested headless (Node) for numerical stability over 250 steps including
runtime particle growth. Rendering not covered — needs a real browser.
