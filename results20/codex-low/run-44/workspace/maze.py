#!/usr/bin/env python3
"""Terminal maze generator and solver (no third-party dependencies)."""

import argparse
import random
import sys
import time


def generate_backtracker(width, height, rng):
    """Recursive backtracker (depth-first) maze. Produces perfect mazes."""
    # grid[y][x] is a bitmask of open directions:
    # 1=N, 2=E, 4=S, 8=W
    grid = [[0] * width for _ in range(height)]
    stack = [(0, 0)]
    visited = {(0, 0)}
    dirs = ((0, -1, 1, 4), (1, 0, 2, 8), (0, 1, 4, 1), (-1, 0, 8, 2))

    while stack:
        x, y = stack[-1]
        options = []
        for dx, dy, bit, opp in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                options.append((nx, ny, bit, opp))
        if not options:
            stack.pop()
            continue
        nx, ny, bit, opp = rng.choice(options)
        grid[y][x] |= bit
        grid[ny][nx] |= opp
        visited.add((nx, ny))
        stack.append((nx, ny))
    return grid


def generate_kruskal(width, height, rng):
    """Kruskal's algorithm with random edge weights. Produces perfect mazes."""
    parent = list(range(width * height))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    grid = [[0] * width for _ in range(height)]
    edges = []
    for y in range(height):
        for x in range(width):
            if x + 1 < width:
                edges.append((x, y, x + 1, y))
            if y + 1 < height:
                edges.append((x, y, x, y + 1))
    rng.shuffle(edges)

    for x1, y1, x2, y2 in edges:
        a = find(y1 * width + x1)
        b = find(y2 * width + x2)
        if a == b:
            continue
        parent[a] = b
        if x1 != x2:
            grid[y1][x1] |= 2
            grid[y2][x2] |= 8
        else:
            grid[y1][x1] |= 4
            grid[y2][x2] |= 1
    return grid


GENERATORS = {
    "backtracker": generate_backtracker,
    "kruskal": generate_kruskal,
}


def braid(grid, rng, p=0.3):
    """Remove some dead ends by opening a random blocked wall."""
    h, w = len(grid), len(grid[0])
    for y in range(h):
        for x in range(w):
            if _open_count(grid, x, y) == 1 and rng.random() < p:
                dirs = [(0, -1, 1, 4), (1, 0, 2, 8), (0, 1, 4, 1), (-1, 0, 8, 2)]
                rng.shuffle(dirs)
                for dx, dy, bit, opp in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not (grid[y][x] & bit):
                        grid[y][x] |= bit
                        grid[ny][nx] |= opp
                        break
    return grid


def _open_count(grid, x, y):
    return bin(grid[y][x]).count("1")


def solve_astar(grid, start, goal):
    """A* with Manhattan heuristic. Returns a path or None."""
    h, w = len(grid), len(grid[0])

    def heuristic(x, y):
        return abs(x - goal[0]) + abs(y - goal[1])

    open_set = {start: 0}
    came_from = {}
    g = {start: 0}
    dirs = ((0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8))

    while open_set:
        current = min(open_set, key=lambda p: g[p] + heuristic(*p))
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        del open_set[current]
        x, y = current
        for dx, dy, bit in dirs:
            if not (grid[y][x] & bit):
                continue
            nxt = (x + dx, y + dy)
            ng = g[current] + 1
            if ng < g.get(nxt, float("inf")):
                came_from[nxt] = current
                g[nxt] = ng
                open_set[nxt] = ng
    return None


def solve_bfs(grid, start, goal):
    """Breadth-first search for the shortest path (unweighted edges)."""
    h, w = len(grid), len(grid[0])
    frontier = [start]
    came_from = {start: None}
    dirs = ((0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8))

    for current in frontier:
        if current == goal:
            break
        x, y = current
        for dx, dy, bit in dirs:
            if not (grid[y][x] & bit):
                continue
            nxt = (x + dx, y + dy)
            if nxt not in came_from:
                came_from[nxt] = current
                frontier.append(nxt)

    if goal not in came_from:
        return None
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def render(grid, path=None):
    """Render the maze as ASCII. Open cells are spaces; path cells are dots."""
    h, w = len(grid), len(grid[0])
    pathset = set(path) if path else set()
    cols = 2 * w + 1
    rows = 2 * h + 1
    out = [["#"] * cols for _ in range(rows)]

    for y in range(h):
        for x in range(w):
            cx, cy = 1 + 2 * x, 1 + 2 * y
            out[cy][cx] = "." if (x, y) in pathset else " "
            if grid[y][x] & 1:      # north open
                out[cy - 1][cx] = "." if (x, y) in pathset else " "
            if grid[y][x] & 4:      # south open
                out[cy + 1][cx] = "." if (x, y) in pathset else " "
            if grid[y][x] & 2:      # east open
                out[cy][cx + 1] = "."
            if grid[y][x] & 8:      # west open
                out[cy][cx - 1] = "."

    return "\n".join("".join(row) for row in out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate and solve mazes in the terminal (zero dependencies)."
    )
    parser.add_argument("-W", "--width", type=int, default=15)
    parser.add_argument("-H", "--height", type=int, default=11)
    parser.add_argument(
        "-a", "--algorithm",
        choices=sorted(GENERATORS),
        default="backtracker",
        help="maze generation algorithm",
    )
    parser.add_argument("-b", "--braid", type=float, default=0.0,
                        help="fraction (0-1) of dead ends to open, creating loops")
    parser.add_argument("-s", "--solver", choices=["astar", "bfs"],
                        default="astar", help="pathfinding algorithm")
    parser.add_argument("--show-path", action="store_true",
                        help="draw the solution path on the maze")
    parser.add_argument("--seed", type=int, default=None,
                        help="random seed for reproducible mazes")
    args = parser.parse_args(argv)

    if args.width < 2 or args.height < 2:
        parser.error("width and height must be at least 2")
    if not 0.0 <= args.braid <= 1.0:
        parser.error("--braid must be between 0 and 1")

    rng = random.Random(args.seed)
    gen = GENERATORS[args.algorithm]
    grid = gen(args.width, args.height, rng)
    if args.braid:
        grid = braid(grid, rng, args.braid)

    start = (0, 0)
    goal = (args.width - 1, args.height - 1)

    if args.solver == "astar":
        path = solve_astar(grid, start, goal)
    else:
        path = solve_bfs(grid, start, goal)

    if path is None:
        print("No path found?! (shouldn't happen)", file=sys.stderr)
        return 1

    if args.show_path:
        print(render(grid, path=path))
        print(f"\nSolution: {len(path)} steps "
              f"({len(path)-1} moves) via {args.solver}")
    else:
        print(render(grid))
        print(f"\nGenerated {args.width}x{args.height} {args.algorithm} maze "
              f"(braid={args.braid:.0%})")

    # quick validation
    if not args.show_path:
        again = solve_bfs(grid, start, goal)
        assert again is not None, "maze is not solvable!"
    return 0


if __name__ == "__main__":
    sys.exit(main())
