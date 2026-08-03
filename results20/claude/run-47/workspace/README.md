# life.py — Conway’s Game of Life in the terminal

A dependency-free cell automaton using only Python’s stdlib `curses`. No pip
packages, no internet, just:

```bash
python3 life.py            # start with an empty board
python3 life.py --random   # start with a random fill
python3 life.py -w 160 -h 50   # custom universe size
```

## Controls

| Key | Action |
|-----|--------|
| arrows / `h j k l` | move cursor |
| `space` | toggle cell under cursor (draw / erase) |
| `p` | stamp the current preset at the cursor |
| `Tab` | cycle presets |
| `s` | run / pause the simulation |
| `+` / `-` | faster / slower |
| `n` | single-step one generation (while paused) |
| `c` | clear the board |
| `r` | random fill |
| `q` / `Esc` | quit |

## Preset patterns

Cycle with `Tab`, then stamp with `p`: glider, blinker, pulsar,
**Gosper glider gun** (an infinite glider factory), R-pentomino (a tiny
"methuselah" seed that evolves chaotically for generations), a block-laying
switch engine, and a paired glider. The universe wraps around toroidally —
gliders fly off one edge and reappear on the other.

## Quick story to try

1. `python3 life.py`
2. `Tab` to `gosper`, move to a spot, `p`, then `s`.
3. Watch the gun fire gliders that eventually loop back across the torus.
4. `c`, `Tab` to `methuselah`, `p`, `s` — one tiny seed that lives for 1103
   generations before settling.

The engine (`step`) is a plain pure function, so it’s easy to import and embed
in other scripts: `from life import step`.
