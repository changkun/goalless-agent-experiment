# 2048 (terminal)

A small, polished 2048 game for your terminal. Stdlib only — no install, no deps.

## Play it

```bash
python3 twenty48.py
```

Controls: arrow keys (or `h`/`j`/`k`/`l` or `w`/`a`/`s`/`d`). `r` to restart, `q` to quit.

Useful flags:
- `--seed N` — reproducible game.
- `--ai` — watch a simple greedy AI play itself (no input needed).
- `--test` — run the self-test suite.

## Design notes

- `Game` holds the board, score, move count, and a dedicated `random.Random` for spawns (so the seed actually works).
- `_slide_row_left` is the only piece of merge logic; `move` reduces every other direction to a row-slice with a reverse.
- The AI picks a direction that maximizes the count of "mergeable pairs" after the move, with a corner-preference tiebreaker (down/left before up/right).
- `_supports_color` checks `NO_COLOR` and `sys.stdout.isatty()` so piped output and CI logs stay clean.
