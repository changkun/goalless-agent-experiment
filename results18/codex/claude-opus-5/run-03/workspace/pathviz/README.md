# pathviz

Terminal maze generator and pathfinding visualizer. Generates a perfect maze (or
a weighted open field), runs a search algorithm on it, and animates the frontier
expanding toward the goal in your terminal.

```
python3 -m pathviz --width 31 --height 15 --algo astar --animate
```

## Features

- **Maze generators**: `backtracker` (perfect maze), `prim` (perfect maze, bushier),
  `rooms` (open field with random walls) — all seedable for reproducible runs.
- **Terrain weights**: cells can cost more than 1 step, so `dijkstra`/`astar`
  produce genuinely different paths than `bfs`.
- **Algorithms**: `bfs`, `dfs`, `dijkstra`, `astar`, each returning the full visit
  order so the search can be replayed frame by frame.
- **Rendering**: unicode/ASCII output with optional ANSI colors, plus a
  side-by-side `--compare` mode and a stats table.

## Usage

```
python3 -m pathviz --help
python3 -m pathviz --algo bfs --seed 7                 # single run, final frame
python3 -m pathviz --algo dijkstra --weights --animate # watch costs matter
python3 -m pathviz --compare --seed 7                  # all algorithms, stats only
```

Legend: `#` wall, `.` unvisited floor, `o` visited, `+` frontier, `*` final path,
`S` start, `G` goal. Heavier terrain is shaded `,`/`:`/`;` by cost.

## Tests

```
python3 -m unittest discover -s pathviz/tests -t . -q
```
