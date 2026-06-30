#!/usr/bin/env python3
"""
Elementary Cellular Automata Explorer

Each of the 256 rules maps a 3-cell neighborhood to 0 or 1.
Some produce chaos, some produce fractals, some produce nothing.
Rule 30 → cryptographic randomness. Rule 110 → Turing-complete.
Rule 90 → Sierpiński triangle. Rule 184 → traffic flow model.
"""

import sys
import time
import shutil
import argparse
import random


PALETTE = {
    "fire":    ["\033[90m·", "\033[33m▒", "\033[91m█", "\033[97m▓"],
    "ocean":   ["\033[90m·", "\033[34m░", "\033[36m▒", "\033[96m█"],
    "forest":  ["\033[90m·", "\033[32m░", "\033[92m▒", "\033[32m█"],
    "classic": ["\033[90m·", "\033[97m█"],
    "mono":    [" ", "█"],
}

NAMED_RULES = {
    30:  "Chaos / RNG",
    45:  "Complex",
    60:  "Sierpiński-like",
    90:  "Sierpiński triangle",
    99:  "Dendrite",
    105: "Complementary",
    110: "Turing-complete",
    122: "Striped chaos",
    150: "Symmetric fractal",
    184: "Traffic flow",
    210: "Nested triangles",
    225: "Inverted Sierpiński",
}

RESET = "\033[0m"


def rule_lookup(rule_number: int) -> dict:
    """Decode rule number into a neighborhood→state mapping."""
    table = {}
    for pattern in range(8):
        left  = (pattern >> 2) & 1
        center= (pattern >> 1) & 1
        right = (pattern >> 0) & 1
        table[(left, center, right)] = (rule_number >> pattern) & 1
    return table


def evolve(row: list[int], table: dict) -> list[int]:
    n = len(row)
    return [
        table[(row[(i - 1) % n], row[i], row[(i + 1) % n])]
        for i in range(n)
    ]


def render_row(row: list[int], palette: list[str], density_map: list[int] | None = None) -> str:
    chars = []
    for i, cell in enumerate(row):
        if cell == 0:
            chars.append(palette[0] + RESET)
        else:
            if density_map and len(palette) > 2:
                heat = min(density_map[i], len(palette) - 1)
                chars.append(palette[heat] + RESET)
            else:
                chars.append(palette[-1] + RESET)
    return "".join(chars)


def run(rule_number: int, palette_name: str, speed: float, seed: str, rows: int | None):
    term_cols, term_rows = shutil.get_terminal_size((80, 24))
    width = term_cols
    display_rows = (rows or term_rows) - 4

    table   = rule_lookup(rule_number)
    palette = PALETTE.get(palette_name, PALETTE["classic"])
    label   = NAMED_RULES.get(rule_number, "")

    # Seed the first generation
    if seed == "center":
        row = [0] * width
        row[width // 2] = 1
    elif seed == "random":
        row = [random.randint(0, 1) for _ in range(width)]
    elif seed == "left":
        row = [0] * width
        row[0] = 1
    else:
        row = [0] * width
        row[width // 2] = 1

    # Density tracking for heat-map coloring
    density = [0] * width

    header = f"\033[1mRule {rule_number}\033[0m"
    if label:
        header += f"  \033[90m({label})\033[0m"
    header += f"   palette={palette_name}   seed={seed}"
    header += f"   \033[90mCtrl-C to quit\033[0m"

    print("\033[2J\033[H", end="")  # clear screen
    print(header)
    print("\033[90m" + "─" * width + RESET)

    generation = 0
    try:
        while True:
            # Update density
            for i, c in enumerate(row):
                if c:
                    density[i] = min(density[i] + 1, len(palette) - 1)
                else:
                    density[i] = max(density[i] - 1, 0)

            print(render_row(row, palette, density))
            generation += 1

            row = evolve(row, table)

            if display_rows and generation >= display_rows:
                # Scroll: move cursor to row 3, redraw from there
                if rows:
                    break
                print(f"\033[{display_rows + 2}H", end="")  # reposition
                generation = 0
                row = [0] * width
                if seed == "center":
                    row[width // 2] = 1
                elif seed == "random":
                    row = [random.randint(0, 1) for _ in range(width)]
                density = [0] * width
                print("\033[2J\033[H", end="")
                print(header)
                print("\033[90m" + "─" * width + RESET)

            time.sleep(speed)

    except KeyboardInterrupt:
        print(f"\n\033[90mStopped after {generation} generations.\033[0m")


def demo():
    """Show a quick sampler of interesting rules."""
    term_cols, _ = shutil.get_terminal_size((80, 24))
    width = min(term_cols, 100)
    lines_per_rule = 12

    print("\033[2J\033[H", end="")
    print("\033[1mElementary Cellular Automata — Sampler\033[0m")
    print()

    showcase = [90, 30, 110, 184, 60, 150]

    for rule_number in showcase:
        table  = rule_lookup(rule_number)
        label  = NAMED_RULES.get(rule_number, "")
        row    = [0] * width
        row[width // 2] = 1
        density = [0] * width

        title = f"\033[1mRule {rule_number}\033[0m"
        if label:
            title += f"  \033[33m{label}\033[0m"
        print(title)

        for _ in range(lines_per_rule):
            for i, c in enumerate(row):
                density[i] = min(density[i] + c, 3)

            chars = []
            for i, cell in enumerate(row):
                if cell == 0:
                    chars.append("\033[90m·\033[0m")
                else:
                    heat = min(density[i], 3)
                    color = ["\033[97m", "\033[93m", "\033[91m", "\033[95m"][heat]
                    chars.append(color + "█\033[0m")
            print("".join(chars))

            row = evolve(row, table)

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Elementary Cellular Automata Explorer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Notable rules:
  30   Chaos — used in Mathematica's random number generator
  90   Sierpiński triangle — Pascal's triangle mod 2
  110  Turing-complete — can simulate any computation
  184  Traffic flow — models highway congestion

Palettes: fire, ocean, forest, classic, mono
Seeds:    center, random, left
        """
    )
    parser.add_argument("rule", nargs="?", type=int, help="Rule number 0–255 (omit for demo)")
    parser.add_argument("--palette", "-p", default="fire", choices=PALETTE.keys())
    parser.add_argument("--speed",   "-s", type=float, default=0.04, help="Seconds per generation")
    parser.add_argument("--seed",    "-S", default="center", choices=["center", "random", "left"])
    parser.add_argument("--rows",    "-r", type=int, default=None, help="Stop after N rows")
    parser.add_argument("--demo",    "-d", action="store_true", help="Show sampler of interesting rules")
    args = parser.parse_args()

    if args.demo or args.rule is None:
        demo()
    else:
        if not 0 <= args.rule <= 255:
            print("Rule must be 0–255", file=sys.stderr)
            sys.exit(1)
        run(args.rule, args.palette, args.speed, args.seed, args.rows)


if __name__ == "__main__":
    main()
