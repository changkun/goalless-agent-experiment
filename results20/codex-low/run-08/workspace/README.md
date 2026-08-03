# gol.py — Conway's Game of Life in your terminal

A zero-dependency, single-file Python implementation of Conway's Game of Life
that animates in the terminal.

## Usage

```bash
# Run the classic glider
./gol.py glider

# A random seed
./gol.py random

# A bigger grid, slower
./gol.py pulsar --width 80 --height 30 --fps 8

# Run exactly 10 generations then exit
./gol.py random -g 10

# Wrap edges so the grid behaves like a torus
./gol.py lwss --wrap
```

List all available patterns:

```bash
./gol.py --list
```

## Controls

- `Ctrl+C` stops the animation and clears the screen.

## Patterns

- `blinker` — 3-cell oscillator (period 2)
- `block` — 4-cell still life
- `beehive` — 6-cell still life
- `glider` — 5-cell spaceship that travels diagonally
- `lwss` — lightweight spaceship
- `pulsar` — 48-cell oscillator (period 3)
- `random` — randomly seeded grid (`--density` controls the fill, default 0.35)

## Rules

Each cell looks at its 8 neighbors:

- A live cell survives if it has 2 or 3 neighbors; otherwise it dies.
- A dead cell becomes alive if it has exactly 3 neighbors.

Run `python3 gol.py --help` for the full option list.
