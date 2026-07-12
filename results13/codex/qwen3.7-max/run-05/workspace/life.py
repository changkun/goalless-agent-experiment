#!/usr/bin/env python3
"""Conway's Game of Life — Terminal Edition"""

import os
import sys
import time
import shutil
import random
import argparse
from collections import defaultdict

# ── Patterns ─────────────────────────────────────────────────────────────────

PATTERNS = {
    "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "blinker": [(0, 0), (0, 1), (0, 2)],
    "toad": [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
    "beacon": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)],
    "pulsar": [
        (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
        (2, 0), (2, 5), (2, 7), (2, 12),
        (3, 0), (3, 5), (3, 7), (3, 12),
        (4, 0), (4, 5), (4, 7), (4, 12),
        (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
        (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
        (8, 0), (8, 5), (8, 7), (8, 12),
        (9, 0), (9, 5), (9, 7), (9, 12),
        (10, 0), (10, 5), (10, 7), (10, 12),
        (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10),
    ],
    "lwss": [(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)],
    "pentadecathlon": [
        (0, 1), (1, 1), (2, 0), (2, 2), (3, 1), (4, 1),
        (5, 1), (6, 1), (7, 0), (7, 2), (8, 1), (9, 1),
    ],
    "gosper_glider_gun": [
        (0, 24), (1, 22), (1, 24), (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
        (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35), (4, 0), (4, 1), (4, 10),
        (4, 16), (4, 20), (4, 21), (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17),
        (5, 22), (5, 24), (6, 10), (6, 16), (6, 24), (7, 11), (7, 15), (8, 12), (8, 13),
    ],
    "diehard": [(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)],
    "acorn": [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)],
    "rpentomino": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
}

# ── Color palettes ───────────────────────────────────────────────────────────

PALETTES = {
    "neon": {
        "alive": ["\033[92m", "\033[96m", "\033[93m", "\033[95m"],
        "dead": "\033[38;5;236m",
        "border": "\033[38;5;240m",
        "reset": "\033[0m",
    },
    "fire": {
        "alive": ["\033[91m", "\033[93m", "\033[33m", "\033[38;5;208m"],
        "dead": "\033[38;5;235m",
        "border": "\033[38;5;240m",
        "reset": "\033[0m",
    },
    "ocean": {
        "alive": ["\033[94m", "\033[96m", "\033[34m", "\033[38;5;45m"],
        "dead": "\033[38;5;234m",
        "border": "\033[38;5;240m",
        "reset": "\033[0m",
    },
    "matrix": {
        "alive": ["\033[92m", "\033[32m", "\033[38;5;46m", "\033[38;5;82m"],
        "dead": "\033[38;5;233m",
        "border": "\033[38;5;238m",
        "reset": "\033[0m",
    },
}

# ── Game engine ──────────────────────────────────────────────────────────────

class GameOfLife:
    def __init__(self, width, height, wrap=True):
        self.width = width
        self.height = height
        self.wrap = wrap
        self.cells = set()
        self.age_map = {}
        self.generation = 0
        self.history = []

    def place(self, row, col):
        self.cells.add((row, col))
        self.age_map[(row, col)] = 0

    def place_pattern(self, pattern, offset_row=0, offset_col=0):
        for r, c in pattern:
            self.place(r + offset_row, c + offset_col)

    def randomize(self, density=0.3, seed=None):
        if seed is not None:
            random.seed(seed)
        self.cells.clear()
        self.age_map.clear()
        for r in range(self.height):
            for c in range(self.width):
                if random.random() < density:
                    self.place(r, c)

    def neighbors(self, row, col):
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if self.wrap:
                    nr %= self.height
                    nc %= self.width
                elif nr < 0 or nr >= self.height or nc < 0 or nc >= self.width:
                    continue
                if (nr, nc) in self.cells:
                    count += 1
        return count

    def step(self):
        new_cells = set()
        new_age = {}
        candidates = set(self.cells)
        for r, c in self.cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if self.wrap:
                        nr %= self.height
                        nc %= self.width
                    elif nr < 0 or nr >= self.height or nc < 0 or nc >= self.width:
                        continue
                    candidates.add((nr, nc))

        for pos in candidates:
            n = self.neighbors(pos[0], pos[1])
            alive = pos in self.cells
            if alive and n in (2, 3):
                new_cells.add(pos)
                new_age[pos] = self.age_map.get(pos, 0) + 1
            elif not alive and n == 3:
                new_cells.add(pos)
                new_age[pos] = 0

        pop = len(self.cells)
        self.history.append(pop)
        self.cells = new_cells
        self.age_map = new_age
        self.generation += 1

    def population(self):
        return len(self.cells)


# ── Renderer ─────────────────────────────────────────────────────────────────

CELL_CHARS = ["█", "▓", "▒", "░"]
DEAD_CHAR = "·"

def render(game, palette, use_color=True, show_stats=True, frame=None):
    cols, rows = shutil.get_terminal_size((80, 24))
    grid_h = game.height
    grid_w = game.width * 2  # each cell is 2 chars wide for square-ish look

    buf = []
    p = palette
    rst = p["reset"] if use_color else ""
    dead_c = p["dead"] if use_color else ""
    border_c = p["border"] if use_color else ""

    # Top border
    buf.append(f"{border_c}╔{'══' * game.width}╗{rst}")

    for r in range(game.height):
        line = f"{border_c}║{rst}"
        for c in range(game.width):
            if (r, c) in game.cells:
                age = game.age_map.get((r, c), 0)
                ci = min(age, len(p["alive"]) - 1)
                ch = CELL_CHARS[min(age, len(CELL_CHARS) - 1)]
                color = p["alive"][ci] if use_color else ""
                line += f"{color}{ch}{ch}{rst}"
            else:
                line += f"{dead_c}{DEAD_CHAR} {rst}"
        line += f"{border_c}║{rst}"
        buf.append(line)

    # Bottom border
    buf.append(f"{border_c}╚{'══' * game.width}╝{rst}")

    if show_stats:
        pop = game.population()
        gen = game.generation
        status = f" Gen: {gen:>5} │ Pop: {pop:>5} │ Palette: {palette_name} "
        if frame is not None:
            status += f"│ FPS target: {frame} "
        buf.append(f"{border_c}{status}{rst}")

    return "\n".join(buf)


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life — Terminal Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python life.py                     # Random soup, neon palette
  python life.py -p pulsar           # Place a pulsar
  python life.py -p gosper_glider_gun --palette fire
  python life.py --width 60 --height 30 --speed 0.05
  python life.py --list-patterns     # Show available patterns
  python life.py --list-palettes     # Show available palettes
        """,
    )
    parser.add_argument("--width", "-W", type=int, default=40, help="Grid width (default: 40)")
    parser.add_argument("--height", "-H", type=int, default=20, help="Grid height (default: 20)")
    parser.add_argument("--speed", "-s", type=float, default=0.08, help="Delay between generations (default: 0.08s)")
    parser.add_argument("--density", "-d", type=float, default=0.3, help="Random fill density (default: 0.3)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible fills")
    parser.add_argument("--offset-row", type=int, default=None, help="Pattern row offset (None = center)")
    parser.add_argument("--offset-col", type=int, default=None, help="Pattern col offset (None = center)")
    parser.add_argument("--pattern", "-p", type=str, default=None, help="Pattern to seed (see --list-patterns)")
    parser.add_argument("--palette", type=str, default="neon", choices=PALETTES.keys(), help="Color palette")
    parser.add_argument("--no-wrap", action="store_true", help="Disable toroidal wrapping")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--max-gen", "-m", type=int, default=0, help="Stop after N generations (0=infinite)")
    parser.add_argument("--list-patterns", action="store_true", help="List available patterns and exit")
    parser.add_argument("--list-palettes", action="store_true", help="List available palettes and exit")
    return parser.parse_args()


def main():
    global palette_name
    args = parse_args()

    if args.list_patterns:
        print("Available patterns:")
        for name, cells in PATTERNS.items():
            max_r = max(r for r, c in cells) + 1
            max_c = max(c for r, c in cells) + 1
            print(f"  {name:25s} ({len(cells)} cells, {max_r}x{max_c})")
        return

    if args.list_palettes:
        print("Available palettes:")
        for name in PALETTES:
            print(f"  {name}")
        return

    palette_name = args.palette
    palette = PALETTES[palette_name]
    use_color = not args.no_color

    game = GameOfLife(args.width, args.height, wrap=not args.no_wrap)

    if args.pattern:
        if args.pattern not in PATTERNS:
            print(f"Unknown pattern: {args.pattern}")
            print(f"Available: {', '.join(PATTERNS.keys())}")
            sys.exit(1)
        pattern = PATTERNS[args.pattern]
        max_r = max(r for r, c in pattern) + 1
        max_c = max(c for r, c in pattern) + 1
        off_r = (args.height - max_r) // 2
        off_c = (args.width - max_c) // 2
        game.place_pattern(pattern, off_r, off_c)
    else:
        game.randomize(args.density)

    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            # Clear screen + render
            sys.stdout.write("\033[H\033[2J")
            frame = int(1 / args.speed) if args.speed > 0 else 0
            output = render(game, palette, use_color=use_color, show_stats=True, frame=frame)
            sys.stdout.write(output)
            sys.stdout.flush()

            if args.max_gen > 0 and game.generation >= args.max_gen:
                break

            # Check for extinction or stillness
            if game.population() == 0:
                sys.stdout.write(f"\n\033[91m☠ Extinction at generation {game.generation}\033[0m\n")
                break

            time.sleep(args.speed)
            game.step()

    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        print(f"\n\033[93m⏹ Stopped at generation {game.generation} (population: {game.population()})\033[0m")


if __name__ == "__main__":
    main()
