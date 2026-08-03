"""A small library of well-known Game of Life patterns.

Each pattern is described either as a list-of-strings grid (``#``/``O`` mark
a live cell) or as an RLE string (canonical run-length encoding used by the
ConwayLife community). ``build`` returns a set of live ``(x, y)``
coordinates with the pattern's top-left corner at ``(0, 0)``.
"""


def _from_grid(rows):
    return {
        (x, y)
        for y, row in enumerate(rows)
        for x, ch in enumerate(row)
        if ch in "#O"
    }


def _from_rle(rle):
    """Decode a (body-only) RLE string into a set of live cells.

    Tags ``2o`` etc. are the usual: ``o`` = live, ``b`` = dead run, ``$`` =
    newline, ``!`` = end.
    """
    cells = set()
    x = y = 0
    count = 1
    i = 0
    while i < len(rle):
        ch = rle[i]
        if ch.isdigit():
            j = i
            while j < len(rle) and rle[j].isdigit():
                j += 1
            count = int(rle[i:j])
            i = j
            continue
        if ch == "o":
            for k in range(count):
                cells.add((x + k, y))
            x += count
        elif ch == "b":
            x += count
        elif ch == "$":
            y += count
            x = 0
        elif ch == "!":
            break
        count = 1
        i += 1
    return cells


_PATTERNS = {
    # Stable: never changes.
    "block": _from_grid(["##", "##"]),
    "beehive": _from_grid([".##.", "#..#", ".##."]),
    # Oscillators.
    "blinker": _from_grid(["#", "#", "#"]),
    "toad": _from_grid([".###", "###."]),
    "pulsar": _from_grid([
        "..OOO...OOO..",
        ".............",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        ".............",
        "..OOO...OOO..",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        ".............",
        "..OOO...OOO..",
    ]),
    # Glider: travels diagonally; one period is 4 generations.
    "glider": _from_grid([".O.", "..O", "OOO"]),
    # Lightweight spaceship: travels sideways; one period is 4 generations.
    "lwss": _from_grid([".O..O", "O....", "O...O", "OOOO."]),
    # "Gosper glider gun" — emits a glider every 30 generations.
    # Canonical RLE from the LifeWiki.
    "gosper-gun": _from_rle(
        "24bo11b$22bobo11b$12b2o6b2o12b2o$11bo3bo4b2o12b2o$"
        "2o8bo5bo3b2o14b$2o8bo3bob2o4bobo11b$10bo5bo7bo11b$"
        "11bo3bo20b$12b2o!"
    ),
}

#: Largest period oscillator, with spaceships/guns marked by a period of
#: ``None`` (they translate or emit, so they never return to their seed).
PERIODS = {
    "block": 1,
    "beehive": 1,
    "blinker": 2,
    "toad": 2,
    "pulsar": 3,
    "glider": None,
    "lwss": None,
    "gosper-gun": None,
}


def build(name):
    """Build the named pattern as a set of live (x, y) coordinates."""
    return set(_PATTERNS[name])


def names():
    """Return the names of all available patterns."""
    return tuple(_PATTERNS)
