# golife

A zero-dependency [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
that runs right in your terminal.

## Install

```bash
pip install -e .
```

Or run it directly without installing:

```bash
python3 -m golife.cli glider
```

## Usage

```bash
golife                     # animate a glider, 50 generations
golife pulsar -g 100       # a pulsar for longer
golife --random -s 42      # random soup with a seed
golife -g 20 --nongui      # print only the final frame
golife --list              # list all built-in patterns
cat soup.txt | golife -    # load a pattern from stdin ("O", "*", "#")
```

Options are documented with `golife --help`.

## Patterns

`block`, `beehive`, `blinker`, `toad`, `beacon`, `glider`, `lwss`,
`r_pentomino`, `pulsar`.

## Design

- The universe is an **infinite plane**: live cells are stored as `(x, y)`
  coordinates in a set, so there is no fixed grid size and patterns can drift
  forever.
- Each tick counts neighbours by walking the 8-cell neighbourhood of every
  live cell, then applies the classic birth/survival rules.
- Rendering defaults to a tight crop around the population, or centres the
  population in a fixed `-w`/`-H` area.
- The engine (`golife/engine.py`) has no UI dependencies, so it is trivially
  testable.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
