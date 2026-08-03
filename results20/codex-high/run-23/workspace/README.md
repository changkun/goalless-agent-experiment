# 2048 Terminal

A tiny, dependency-free implementation of **2048** that runs right in your terminal.

## Features
- Pure Python, standard library only (no installs needed)
- Classic merge mechanics: slide, combine equal tiles, spawn a `2` (90%) or `4` (10%)
- Score tracking and win detection
- Configurable board size and winning target

## Play

```bash
python3 -m game2048
```

### Controls

| Key | Action |
|-----|--------|
| `W` / `A` / `S` / `D` | Move up / left / down / right |
| `Q` or `Esc` | Quit |

### Options

```bash
python3 -m game2048 --size 5          # 5x5 board
python3 -m game2048 --target 4096     # win only when you reach 4096
python3 -m game2048 --seed 42         # reproducible board
```

## Run the tests

```bash
python3 -m unittest discover -s tests
```

## Layout

- `game2048/core.py` — pure game logic (board, moves, scoring, win/lose)
- `game2048/__main__.py` — terminal UI and keyboard handling
- `tests/test_core.py` — unit tests for the core logic

## License

MIT
