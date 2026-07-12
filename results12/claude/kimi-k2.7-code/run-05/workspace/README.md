# Conway's Game of Life

A tiny, self-contained terminal implementation of [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) written in Python.

## Run it

```bash
python game_of_life.py
```

The default is a random starting grid. Press `Ctrl-C` to stop.

## Patterns

Pass any of these as the first argument:

- `random` — random soup
- `glider` — classic spaceship
- `blinker` — period-2 oscillator
- `beacon` — period-2 oscillator
- `toad` — period-2 oscillator
- `rpentomino` — small but long-lived methuselah
- `gosper` — Gosper glider gun
- `diehard` — a pattern that disappears after 130 generations

## Options

| Flag | Description |
|------|-------------|
| `-d, --density` | Density for random pattern (0.0–1.0) |
| `-g, --generations` | Stop after N generations |
| `-s, --speed` | Seconds between generations |
| `--no-clear` | Print frames instead of clearing the screen |

## Examples

```bash
python game_of_life.py gosper
python game_of_life.py random -d 0.15 -s 0.05
python game_of_life.py glider --no-clear -g 20
```

## License

Public domain. Do whatever you like with it.
