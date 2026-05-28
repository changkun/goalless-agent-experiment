import os, time, random

W, H = 60, 25
grid = [[random.randint(0, 1) for _ in range(W)] for _ in range(H)]

def step(g):
    new = [[0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            n = sum(g[(y+dy)%H][(x+dx)%W] for dy in (-1,0,1) for dx in (-1,0,1)) - g[y][x]
            new[y][x] = 1 if n == 3 or (n == 2 and g[y][x]) else 0
    return new

try:
    while True:
        os.system("clear")
        print("\n".join("".join("██" if c else "  " for c in row) for row in grid))
        print("\n  Conway's Game of Life  |  Ctrl+C to quit")
        grid = step(grid)
        time.sleep(0.12)
except KeyboardInterrupt:
    print("\n  Thanks for watching life unfold.")
