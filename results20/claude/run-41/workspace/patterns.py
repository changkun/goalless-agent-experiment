"""Pattern library for the Game of Life, in RLE format.

Each pattern is a name and an RLE string (see
https://conwaylife.com/wiki/Run_Length_Encoded). `parse_rle` turns an RLE
into a list of (row, col) live cells with the bounding box shifted to the
origin, so patterns can be seeded anywhere.

This module has no dependency on `life.py`.
"""

PATTERNS = {
    "glider": {
        "name": "Glider",
        "rle": (
            "bob$\n"
            "2bo$\n"
            "3o!"
        ),
    },
    "blinker": {
        "name": "Blinker",
        "rle": (
            "3o!"
        ),
    },
    "block": {
        "name": "Block",
        "rle": (
            "2o$\n"
            "2o!"
        ),
    },
    "pulsar": {
        "name": "Pulsar",
        "rle": (
            "2b3o3b3o2b2$\n"
            "o4bobo4bo$\n"
            "o4bobo4bo$\n"
            "o4bobo4bo$\n"
            "2b3o3b3o2b2$\n"
            "2b3o3b3o2b$\n"
            "o4bobo4bo$\n"
            "o4bobo4bo$\n"
            "o4bobo4bo2$\n"
            "2b3o3b3o!"
        ),
    },
    "gosper_glider_gun": {
        "name": "Gosper Glider Gun",
        "rle": (
            "24bo$\n"
            "22bobo$\n"
            "12b2o6b2o12b2o$\n"
            "11bo3bo4b2o12b2o$\n"
            "2o8bo3bo3b2o14bobo$\n"
            "2o8bo3bo2bobob2o11b2o$\n"
            "10bo3bo2bo13bo$\n"
            "11bo3bo4b2o12b2o$\n"
            "12b2o6b2o12b2o$\n"
            "22bobo$\n"
            "24bo!"
        ),
    },
}


def parse_rle(rle):
    """Parse an RLE string into a set of (row, col) live cells at the origin."""
    cells = set()
    r = c = 0
    count = 0
    for ch in rle:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "b":
            c += count if count else 1
            count = 0
        elif ch == "o":
            n = count if count else 1
            for _ in range(n):
                cells.add((r, c))
                c += 1
            count = 0
        elif ch == "$":
            r += count if count else 1
            c = 0
            count = 0
        elif ch == "!":
            break
        # whitespace and comments are ignored
    return cells


def normalize(cells):
    """Shift a set of cells so the minimum row/col is 0 (at the origin)."""
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    miny, minx = min(ys), min(xs)
    return frozenset((y - miny, x - minx) for y, x in cells)


def find(name):
    """Return (name, cells) for a pattern by key, or None."""
    entry = PATTERNS.get(name)
    if not entry:
        return None
    return entry["name"], normalize(parse_rle(entry["rle"]))


def all_patterns():
    return {name: normalize(parse_rle(entry["rle"])) for name, entry in PATTERNS.items()}


if __name__ == "__main__":
    for name in PATTERNS:
        pretty, cells = find(name)
        ys = [y for y, _ in cells]
        xs = [x for _, x in cells]
        print(f"{pretty}: {len(cells)} cells, {max(ys) + 1} rows x {max(xs) + 1} cols")
