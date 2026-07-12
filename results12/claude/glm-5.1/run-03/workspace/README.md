# ✦ Terminal Cosmology ✦

A tiny collection of beautiful things that run in your terminal.

## 🧬 Conway's Game of Life — `life.py`

An interactive cellular automaton simulator with colorful Unicode rendering.

```
python3 life.py
```

**Controls:**
| Key | Action |
|-----|--------|
| SPACE | Pause / Resume |
| N | Next step (when paused) |
| R | Reset with random cells |
| 1–6 | Load preset pattern |
| + / - | Speed up / Slow down |
| Q | Quit |

**Presets:**
1. Random Soup
2. Gosper Glider Gun (manufactures gliders!)
3. Pulsar (period-3 oscillator)
4. Pentadecathlon (period-15 oscillator)
5. R-pentomino (chaotic methuselah)
6. Diehard (dies after 130 generations)

## 🌌 Galaxy Generator — `galaxy.py`

Generates unique ASCII art spiral galaxies. Each seed produces a different cosmic structure.

```
python3 galaxy.py              # random galaxy
python3 -c "import random; random.seed(42); from galaxy import galaxy; print(galaxy())"
```

## 📸 Demo Mode — `demo.py`

Non-interactive snapshot for headless terminals. Runs the Glider Gun for 50 generations and prints the final state.

```
python3 demo.py
```

---

*Emergence is the deepest magic — simple rules, infinite complexity.*
