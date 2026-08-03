# Conway's Life

A self-contained, single-file implementation of Conway's Game of Life in
vanilla HTML/CSS/JavaScript. No build step, no dependencies.

## Run it

Open `index.html` in any modern browser. You can also serve it locally:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Controls

- **Click / drag** on the grid to paint living cells.
- **Right-click or hold Shift** while dragging to erase.
- **Start / Pause** — toggles the simulation loop.
- **Step** — advances a single generation (pauses the loop).
- **Clear** — wipes the grid and resets the generation counter.
- **Randomize** — fills the grid with a random population.
- **Preset** — load a classic pattern (Glider, Gosper Gun, Pulsar, LWSS).
- **Speed slider** — adjusts ticks per second (1–60, live while running).

### Keyboard shortcuts

- `Space` — start/pause
- `N` — advance one generation
- `C` — clear the grid

## Notes

- The grid wraps around (toroidal), so patterns that leave the edge reappear
  on the opposite side.
- Presets are centered automatically and snap to the wrapped grid.
