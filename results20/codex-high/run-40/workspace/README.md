# Conway's Game of Life

A zero-dependency, terminal-based [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) in a single Python file.

## Run

```bash
python3 game_of_life.py
```

## Controls

| Key     | Action                        |
|---------|-------------------------------|
| `space` | pause / resume                |
| `n`     | step one generation (paused)  |
| `s` / `l` | save / load current pattern |
| `c`     | clear the board               |
| `1`–`4` | load built-in presets         |
| `5`     | random soup                   |
| `r`     | randomize                     |
| `?`     | help overlay                  |
| `q` / `ESC` | quit                      |

## Presets

- `1` — glider
- `2` — Gosper glider gun
- `3` — pulsar
- `4` — r-pentomino
- `5` — random soup

## Tests

```bash
python3 -m unittest test_game_of_life.py
```
