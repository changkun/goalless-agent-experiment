# game_of_life

Conway's Game of Life in your terminal — no dependencies beyond the Python
standard library.

## Run

```console
$ python3 -m game_of_life [--pattern blinker|block|glider]
```

## Controls

| Key      | Action                       |
| -------- | ---------------------------- |
| `space`  | Step one generation          |
| `p`      | Toggle pause / play          |
| `r`      | Randomise the board          |
| `c`      | Clear the board              |
| `+` / `-`| Speed up / slow down         |
| mouse    | Toggle cells by hand         |
| `q`      | Quit                         |

## Tests

```console
$ python3 -m game_of_life.__tests__
```

## Notes

- The board is bounded and toroidal: cells wrap around all edges.
- A very small terminal shrinks the board, so patterns may be clipped —
  resize to at least ~40×80 for the default `glider`.
