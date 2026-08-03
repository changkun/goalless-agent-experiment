# Life — cellular automata, pure Python

Conway's Game of Life and friends, in a single self-contained file with
**zero dependencies** (stdlib only). Runs right in the terminal, or exports
a click-to-pause animated HTML page.

## Quick start

```sh
python3 life.py glider life       # a glider gliding away
python3 life.py r-pentomino life  # the famous chaotic seed
python3 life.py soup maze         # random soup under the "maze" rule
python3 life.py --html gosper -o life.html   # then open life.html in a browser
python3 life.py --list            # everything available
```

## Flags

| Flag | Meaning |
|------|---------|
| `g <n>` / `--gens <n>` | run **n** generations (default 120) |
| `--seed <n>` | seed the random soup (default: random) |
| `--html` | write an animated `life.html` instead of animating in terminal |
| `-o <path>` | output path for `--html` |
| `--list` | list patterns and rules |

## Patterns

`glider` · `r-pentomino` · `pulsar` · `gosper` (glider gun) · and `soup` for a
random start.

## Rule sets

Life-like rules are written **B/S** (birth / survive neighbour counts):

- **life** `B3/S23` — Conway's Game of Life
- **highlife** `B36/S23` — Life plus the cell that reproduces at 6
- **seeds** `B2/S` — every live cell dies; pure reproduction
- **daynight** `B3678/S34678` — symmetric, explores stably
- **maze** `B3/S12345` — grows maze corridors
- **pulsar** `B3/S234` — a moving "pulsar"
- **fredkin** — every cell flips at odd neighbour counts

## Example

```sh
python3 life.py r-pentomino life -g 200   # watch it explode and settle
```

## Layout

- `life.py` — everything (engine, patterns, rules, terminal + HTML output)
- `life.html` — generated artifact, open in any browser; click the canvas to
  pause/resume
