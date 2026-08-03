# Terminal 2048

A classic 2048 clone that runs entirely in your terminal. Pure Python
standard library — no dependencies to install.

## Run it

```bash
cd 2048
python3 src/cli.py
```

Use **WASD** or the **arrow keys** to slide the board. Press `q` to quit.
Reach **2048** to win; when no moves remain the game ends.

### Options

```bash
python3 src/cli.py --size 5     # play on a 5x5 board
python3 src/cli.py --seed 42    # deterministic tile spawns
```

## How it plays

- Every move slides all tiles in a direction, merging equal adjacent
  pairs into a single tile worth double.
- After each successful move a new tile (90% `2`, 10% `4`) appears in a
  random empty cell.
- `src/game.py` holds pure game logic (testable, no I/O).
- `src/cli.py` is the interactive terminal front end.

## Tests

```bash
cd 2048
python3 -m unittest discover -s tests -v
```
