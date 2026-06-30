"""Conway's Game of Life, rendered as ANSI frames in the terminal."""
import sys
import time

GLIDER_GUN = [
    (1, 5), (1, 6), (2, 5), (2, 6),
    (11, 5), (11, 6), (11, 7),
    (12, 4), (12, 8),
    (13, 3), (13, 9),
    (14, 3), (14, 9),
    (15, 6),
    (16, 4), (16, 8),
    (17, 5), (17, 6), (17, 7),
    (18, 6),
    (21, 3), (21, 4), (21, 5),
    (22, 3), (22, 4), (22, 5),
    (23, 2), (23, 6),
    (25, 1), (25, 2), (25, 6), (25, 7),
    (35, 3), (35, 4), (36, 3), (36, 4),
]


def step(live, width, height):
    counts = {}
    for (x, y) in live:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % width, (y + dy) % height
                counts[(nx, ny)] = counts.get((nx, ny), 0) + 1
    new_live = set()
    for cell, n in counts.items():
        if n == 3 or (n == 2 and cell in live):
            new_live.add(cell)
    return new_live


def render(live, width, height):
    rows = []
    for y in range(height):
        row = "".join("#" if (x, y) in live else " " for x in range(width))
        rows.append(row)
    return "\n".join(rows)


def main():
    width, height = 50, 20
    live = set(GLIDER_GUN)
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.08

    for i in range(frames):
        sys.stdout.write("\x1b[H\x1b[2J")
        print(f"Conway's Game of Life — gen {i} — {len(live)} live cells\n")
        print(render(live, width, height))
        sys.stdout.flush()
        live = step(live, width, height)
        time.sleep(delay)


if __name__ == "__main__":
    main()
