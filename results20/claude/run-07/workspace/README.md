# glife.py — Conway's Game of Life in your terminal

A zero-dependency, single-file Game of Life that runs with just Python 3.

Live cells **glow** through a color gradient by age (young = bright green-cyan,
old = violet). Dead cells that are about to be born show as faint dots, so you
can see life forming before it sparks.

## Run

```bash
python3 glife.py            # uses your terminal size
python3 glife.py --cols 80 --rows 30 --density 0.22
```

## Controls

| Key       | Action                                    |
|-----------|-------------------------------------------|
| `space`   | pause / resume                            |
| `c`       | clear the board                           |
| `g`       | stamp a **Gosper glider gun** at cursor   |
| `p`       | stamp a **pulsar** at cursor              |
| `+` / `-` | speed up / slow down                      |
| `s`       | single-step (while paused)                |
| `arrows`  | move the stamp cursor                    |
| `q`       | quit                                      |

Press `g` and watch it manufacture gliders endlessly — or `c` then stamp a few
pulsars and let them hum.

## Why

Built as a self-contained, runnable little thing with no dependencies — open
the file, read it, tweak the palette, enjoy the bioluminescence.
