#!/usr/bin/env python3
"""Print every pattern in the library, rendered in its own bounding box."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from patterns import build, names, PERIODS
from render import render_str


def main(argv):
    only = argv[1:] or list(names())
    for name in only:
        if name not in names():
            print(f"Unknown pattern {name!r}")
            return 2
        cells = build(name)
        w = max(x for x, _ in cells) + 1
        h = max(y for _, y in cells) + 1
        period = PERIODS[name]
        kind = ("period %d" % period) if period else "moving/emitting"
        print(f"== {name}  ({len(cells)} cells, {kind}) ==")
        print(render_str(cells, w, h, alive="#", dead="."))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
