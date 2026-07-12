#!/usr/bin/env python3
"""
Snapshot renderer for Game of Life — produces a static frame.
Used for demo/display when no interactive terminal is available.
"""

from life import Grid, PATTERNS, PALETTE, RESET

def render_snapshot(grid, pattern_name=""):
    """Render the grid as a static colored text block."""
    lines = []
    header = f"  ✦ GAME OF LIFE ✦   gen: {grid.generation}   pop: {grid.population}   pattern: {pattern_name}"
    lines.append(header)
    lines.append("  " + "─" * grid.width * 2)

    for y in range(grid.height):
        row = ""
        for x in range(grid.width):
            cell = grid.cells[y][x]
            if cell == 1:
                n = grid.count_neighbors(x, y)
                color = PALETTE[min(n, len(PALETTE) - 1)]
                row += color + "██" + RESET
            else:
                row += "  "
        lines.append("  " + row)

    return "\n".join(lines)


def run_demo(generations=50, width=60, height=20):
    """Run a non-interactive demo, printing the final state."""
    grid = Grid(width, height)

    # Load the Gosper Glider Gun — it's the most beautiful pattern
    _, gun = PATTERNS[2]
    grid.load_pattern(gun)
    pattern_name = "Glider Gun"

    print(f"\n  Running {generations} generations of Conway's Game of Life...\n")

    for i in range(generations):
        grid.step()
        # Show progress every 10 generations
        if (i + 1) % 10 == 0:
            print(f"  ... generation {i+1}, population {grid.population}")

    print()
    print(render_snapshot(grid, pattern_name))
    print()
    print(f"  After {generations} generations: {grid.population} cells alive")
    print(f"  Gliders have been launched! 🚀\n")


if __name__ == "__main__":
    run_demo()
