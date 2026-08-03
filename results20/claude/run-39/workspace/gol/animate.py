#!/usr/bin/env python3
"""Run a live Game of Life animation in the terminal.

Usage:
    python animate.py [pattern] [generations] [width] [height]

Defaults to a Gosper gun with a generous field, which keeps producing
gliders that sail off to the south-east.
"""

import sys
import time

from engine import step_n
from patterns import build, names
from render import render_str


def main(argv):
    name = argv[1] if len(argv) > 1 else "gosper-gun"
    if name not in names():
        print(f"Unknown pattern {name!r}. Known: {', '.join(names())}")
        return 2

    generations = int(argv[2]) if len(argv) > 2 else 60
    width = int(argv[3]) if len(argv) > 3 else 44
    height = int(argv[4]) if len(argv) > 4 else 22
    delay = 0.08

    universe = build(name)
    try:
        for frame in step_n(universe, generations):
            sys.stdout.write("\033[H")           # home cursor
            sys.stdout.write("\033[2J")          # clear screen
            sys.stdout.write(render_str(frame, width, height))
            sys.stdout.flush()
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
