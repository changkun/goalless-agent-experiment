"""Terminal rendering for a Game of Life universe.

``render_row`` and ``render`` only depend on the standard library and take a
plain ASCII character for cells, so the core can be tested headlessly.
"""


def render(live, width, height, alive="#", dead=" "):
    """Render the region ``[0, width) x [0, height)`` as a list of rows.

    Cells outside the region are simply not drawn. The layout matches
    ``patterns.build``: increasing *x* goes right, increasing *y* goes down,
    so a printed pattern looks the way it does as ASCII art.
    """
    return [
        "".join(alive if (x, y) in live else dead for x in range(width))
        for y in range(height)
    ]


def render_str(live, width, height, alive="#", dead=" "):
    """Render as a single newline-joined string (convenience / tests)."""
    return "\n".join(render(live, width, height, alive, dead))
