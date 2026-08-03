# 2048 (Terminal)

A classic sliding-tile puzzle in pure Python, playable right in your terminal.

## How to play

- All tiles slide in the chosen direction and merge when equal (merging once per move).
- Each successful move spawns a new tile (mostly a `2`, sometimes a `4`).
- Reach **2048** to win; the game ends when no moves remain.
- Combine factors add their sums to your score.

## Controls

| Action | Keys |
|---|---|
| Move | Arrow keys, or `w`/`a`/`s`/`d` (also `hjkl`) |
| Quit | `q` or `Ctrl-C` |

## Run it

```bash
python -m game2048
```

Or install it as a command:

```bash
pip install -e .
game2048
```

## Development

Run the test suite (requires `pytest`):

```bash
pip install pytest
python -m pytest
```
