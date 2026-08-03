# critters 🦠

A zero-dependency terminal cellular-automata playground in pure Python
(standard library only, Python 3.10+).

## Quick start

```bash
# Interactive curses mode (needs a real terminal)
python3 critters/critters.py

# Headless ANSI animation: 40 frames of the Gosper glider gun
python3 critters/critters.py --frames 40 --preset glider-gun --delay 0.06

# List everything
python3 critters/critters.py --list
```

## Controls (interactive mode)

| Key     | Action                                   |
| ------- | ---------------------------------------- |
| `space` | pause / resume                           |
| `n`     | step one frame while paused              |
| `r`     | reset with a random soup                 |
| `g`     | reset with a glider                      |
| `p`     | reset with a pulsar                      |
| `q`     | quit                                     |

## Presets

- `random` — random soup (35% density)
- `glider` — the classic five-cell glider
- `glider-gun` — Gosper's glider gun
- `pulsar` — symmetric oscillator
- `spaceships` — a field of light-weight spaceships (LWSS)
- `r-pentomino` — chaotic growth into stable debris

## Rules

- `life` — Conway's Game of Life (B3/S23)
- `highlife` — HighLife (B36/S23)
- `seeds` — Seeds (B2/S0)
- `livesweeper` — Livesweeper (B1/S01234567)

## Design notes

- The grid is rendered at half resolution using Unicode block characters
  (`▀▄█▌▐` etc.), giving a crisper picture in the terminal.
- Rules are pure functions `(grid) -> grid`, so adding a new rule is a
  one-liner registration in the `RULES` table.
- No external dependencies, no build step.
