# Terminal Fireworks

A tiny, dependency-free ASCII fireworks animation for your terminal, built
with Python's standard `curses` module.

## Run it

```bash
python3 fireworks.py
```

Press `q` to quit.

## Options

- `--fps FPS` — frames per second (default: `30`)
- `--density DENSITY` — how often rockets launch; higher is busier (default: `1.0`)

Example:

```bash
python3 fireworks.py --fps 45 --density 1.8
```

Requires a terminal that supports color and a reasonably sized window
(80x24 or larger recommended).
