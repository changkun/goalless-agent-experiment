"""Animate a Game of Life pattern in the terminal: python -m life [pattern]."""

import sys
import time

from .life import PATTERNS, parse, render, step

WIDTH, HEIGHT = 60, 24


def main(argv: list[str]) -> int:
    name = argv[1] if len(argv) > 1 else "gosper-gun"
    if name not in PATTERNS:
        print(f"unknown pattern {name!r}; choose from: {', '.join(PATTERNS)}")
        return 1
    generations = int(argv[2]) if len(argv) > 2 else 200
    board = parse(PATTERNS[name], origin=(2, 2))
    try:
        for gen in range(generations):
            frame = render(board, WIDTH, HEIGHT)
            sys.stdout.write(f"\x1b[H\x1b[2J{frame}\n{name}  gen {gen}  live {len(board)}\n")
            sys.stdout.flush()
            board = step(board)
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
