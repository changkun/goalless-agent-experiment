"""Conway's Game of Life with a Gosper glider gun.

The gun emits one glider every 30 generations — proving life patterns can
grow without bound. Bill Gosper found it in 1970, winning Conway's $50 bet.
"""
import sys
import time

W, H = 60, 30

# Gosper glider gun, offset to fit comfortably in the grid.
GUN = """
........................O...........
......................O.O...........
............OO......OO............OO
...........O...O....OO............OO
OO........O.....O...OO..............
OO........O...O.OO....O.O...........
..........O.....O.......O...........
...........O...O....................
............OO......................
"""


def seed():
    grid = [[0] * W for _ in range(H)]
    for r, line in enumerate(GUN.strip("\n").splitlines()):
        for c, ch in enumerate(line):
            if ch == "O":
                grid[r + 1][c + 1] = 1
    return grid


def step(g):
    nxt = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            n = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W:
                        n += g[rr][cc]
            if g[r][c]:
                nxt[r][c] = 1 if n in (2, 3) else 0
            else:
                nxt[r][c] = 1 if n == 3 else 0
    return nxt


def render(g, gen):
    out = [f"Gen {gen:4d}  |  live: {sum(sum(row) for row in g):4d}"]
    out.append("+" + "-" * W + "+")
    for row in g:
        out.append("|" + "".join("#" if x else " " for x in row) + "|")
    out.append("+" + "-" * W + "+")
    return "\n".join(out)


def main():
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.08
    g = seed()
    for i in range(gens + 1):
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(render(g, i))
        sys.stdout.flush()
        if i < gens:
            g = step(g)
            time.sleep(delay)


if __name__ == "__main__":
    main()
