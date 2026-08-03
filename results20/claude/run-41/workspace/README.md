# Life in the Terminal

Conway's Game of Life running as an interactive **curses** application.
Pure Python, no dependencies — it runs anywhere Python 3 does.

## Run it

```sh
python3 life.py
```

Or with your own grid size / starting pattern:

```sh
python3 life.py --height 40 --width 90 --pattern pulsar
```

## Keys

| Key              | Action                              |
|------------------|-------------------------------------|
| `space`          | play / pause                        |
| `.` `,`          | step forward / back (when paused)   |
| `[` `]`          | slower / faster                     |
| `g`              | load the Gosper glider gun          |
| `p`              | load a pulsar                       |
| `r`              | random soup                         |
| `c`              | clear the board                     |
| `q`              | quit                                |

## Design notes

- The universe is a **torus** — cells wrap around every edge. That keeps the
  math simple and avoids boundary bugs, at the cost of patterns being unable to
  live truly "in isolation" the way they do on an infinite plane.
- The engine keeps only the live cells in a `set` and considers only their
  neighborhoods each generation, so sparse boards run fast (a glider gun on a
  60×80 board runs thousands of generations per second).
- Life, drawing, and the input loop are separated so the engine can be
  imported and unit-tested headlessly.
- Patterns live in `patterns.py` (RLE format), loaded by `life.py`, so the
  engine never hard-codes coordinates.

## Files

| File           | Purpose                                        |
|----------------|------------------------------------------------|
| `life.py`      | curses app: engine + UI                       |
| `patterns.py`  | pattern library (RLE) + parser                |
| `test_life.py` | engine + parser + pattern tests (pytest)      |

## Tests

```sh
python3 -m pytest test_life.py
```

or, with no pytest installed:

```sh
python3 test_life.py
```
