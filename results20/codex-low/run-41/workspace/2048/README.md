# Terminal 2048

A no-dependency, pure-Python clone of 2048 that runs right in your terminal with ANSI colors.

## Run

```bash
python3 game2048.py
```

## Controls

- Arrows or `WASD` — slide tiles (adjacent equal tiles merge toward the direction)
- `r` — restart
- `q` — quit

## Options

```bash
python3 game2048.py --size 4 --goal 2048
python3 game2048.py -n 5 -g 4096 --seed 42
```

- `--size` / `-n` — board size (default `4`)
- `--goal` / `-g` — winning target (default `2048`)
- `--seed` / `-s` — RNG seed for reproducible layouts

## Rules

- Each move slides all tiles and merges equal neighbors once per move; merged pairs score their combined value.
- A move that doesn't change the board spawns no new tile.
- Game over when no cell is empty and no two equal tiles are adjacent.
- Reaching the goal shows a victory banner; you can keep playing.

## Tests

```bash
python3 -m unittest test_game2048.py -v
```
