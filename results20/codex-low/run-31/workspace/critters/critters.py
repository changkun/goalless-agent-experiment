#!/usr/bin/env python3
"""critters -- a zero-dependency terminal cellular-automata playground.

Run interactively (curses):   python3 critters.py
Plot a few frames (ANSI):     python3 critters.py --frames 20 --preset glider-gun
List available presets:       python3 critters.py --list
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

# neighbour offsets for a 2D grid (8-cell Moore neighbourhood, no self)
NEIGHBORS = (
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
)


def step_life(grid: list[list[int]]) -> list[list[int]]:
    """Classic Conway's Game of Life: B3/S23."""
    h, w = len(grid), len(grid[0])
    nxt = [[0] * w for _ in range(h)]
    for y in range(h):
        row = grid[y]
        for x in range(w):
            live = 0
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                    live += 1
            if row[x]:
                nxt[y][x] = 1 if live in (2, 3) else 0
            else:
                nxt[y][x] = 1 if live == 3 else 0
    return nxt


def step_highlife(grid: list[list[int]]) -> list[list[int]]:
    """HighLife: B36/S23 -- births on 3 OR 6 neighbours, same survival."""
    h, w = len(grid), len(grid[0])
    nxt = [[0] * w for _ in range(h)]
    for y in range(h):
        row = grid[y]
        for x in range(w):
            live = 0
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                    live += 1
            if row[x]:
                nxt[y][x] = 1 if live in (2, 3) else 0
            else:
                nxt[y][x] = 1 if live in (3, 6) else 0
    return nxt


def step_seeds(grid: list[list[int]]) -> list[list[int]]:
    """Seeds: B2/S0 -- cells die every tick, births only on exactly 2 neighbours."""
    h, w = len(grid), len(grid[0])
    nxt = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            live = 0
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                    live += 1
            if live == 2:
                nxt[y][x] = 1
    return nxt


def step_livesweeper(grid: list[list[int]]) -> list[list[int]]:
    """Livesweeper (B1/S01234567): a cell is alive if it has exactly 1 neighbour;
    births happen anywhere with exactly 1 alive neighbour, dying otherwise."""
    h, w = len(grid), len(grid[0])
    nxt = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            live = 0
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                    live += 1
            nxt[y][x] = 1 if live == 1 else 0
    return nxt


RULES = {
    "life": (step_life, "Conway's Game of Life (B3/S23)"),
    "highlife": (step_highlife, "HighLife (B36/S23)"),
    "seeds": (step_seeds, "Seeds (B2/S0)"),
    "livesweeper": (step_livesweeper, "Livesweeper (B1/S01234567)"),
}

# ---------------------------------------------------------------------------
# Presets (seeded patterns)
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict] = {
    "random": {
        "desc": "Random soup (classic Conway)",
        "make": lambda w, h: random_grid(w, h, density=0.35),
    },
    "glider": {
        "desc": "Five-cell glider drifting diagonally",
        "make": lambda w, h: stamp(w, h, [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]),
    },
    "glider-gun": {
        "desc": "Gosper glider gun emitting a stream",
        "make": lambda w, h: stamp(w, h, GOSPER_GUN),
    },
    "pulsar": {
        "desc": "Pulsar -- a highly symmetric oscillator",
        "make": lambda w, h: stamp(w, h, PULSAR),
    },
    "spaceships": {
        "desc": "Field of light-weight spaceships (LWSS)",
        "make": lambda w, h: field(w, h, LWSS),
    },
    "r-pentomino": {
        "desc": "R-pentomino: chaotic growth into a stable society",
        "make": lambda w, h: stamp(w, h, R_PENTOMINO),
    },
}

# Gosper glider gun (origin at cell 0,0 as commonly listed)
GOSPER_GUN = [(x, y) for y, row in enumerate([
    "........................O...........",
    "......................O.O...........",
    "............OO......OO............OO",
    "...........O...O....OO............OO",
    "OO........O.....O...OO..............",
    "OO........O...O.OO....O.O...........",
    "..........O.....O.......O...........",
    "...........O...O....................",
    "............OO......................",
]) for x, ch in enumerate(row) if ch == "O"]

# Pulsar oscillator
PULSAR = [(x, y) for y, row in enumerate([
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
]) for x, ch in enumerate(row) if ch == "O"]

# Light-weight spaceship
LWSS = [(x, y) for y, row in enumerate([
    ".X..X",
    "X....",
    "X...X",
    "XXXX.",
]) for x, ch in enumerate(row) if ch == "X"]

# R-pentomino
R_PENTOMINO = [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)]


def random_grid(w: int, h: int, density: float = 0.35) -> list[list[int]]:
    rng = random.Random()
    return [[1 if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]


def stamp(w: int, h: int, cells: list[tuple[int, int]], ox: int = 5, oy: int = 5) -> list[list[int]]:
    """Place a pattern near the top-left corner, centred on its bounding box."""
    minx = min(c[0] for c in cells)
    miny = min(c[1] for c in cells)
    grid = [[0] * w for _ in range(h)]
    for x, y in cells:
        gx, gy = x - minx + ox, y - miny + oy
        if 0 <= gx < w and 0 <= gy < h:
            grid[gy][gx] = 1
    return grid


def field(w: int, h: int, pattern: list[tuple[int, int]], step: int = 8) -> list[list[int]]:
    """Tile a pattern across a grid in a regular field."""
    grid = [[0] * w for _ in range(h)]
    minx = min(c[0] for c in pattern)
    miny = min(c[1] for c in pattern)
    maxx = max(c[0] for c in pattern)
    maxy = max(c[1] for c in pattern)
    pw = (maxx - minx) + 1
    ph = (maxy - miny) + 1
    for oy in range(2, h - ph, step):
        for ox in range(2, w - pw, step):
            for x, y in pattern:
                grid[y - miny + oy][x - minx + ox] = 1
    return grid

# ---------------------------------------------------------------------------
# Rendering (headless ANSI)
# ---------------------------------------------------------------------------

# Block characters: 4 sub-cells per terminal cell (top-left, top-right, bottom-left, bottom-right)
_BLOCKS = [
    " ",            # 0b0000
    "▘",            # 0b0001  top-left
    "▝",            # 0b0010  top-right
    "▀",            # 0b0011  top row
    "▖",            # 0b0100  bottom-left
    "▌",            # 0b0101  left col
    "▞",            # 0b0110  bottom-left + top-right
    "▛",            # 0b0111  top + bottom-left
    "▗",            # 0b1000  bottom-right
    "▚",            # 0b1001  bottom-right + top-left
    "▐",            # 0b1010  right col
    "▜",            # 0b1011  top + bottom-right
    "▄",            # 0b1100  bottom row
    "▙",            # 0b1101  bottom row + top-left
    "▟",            # 0b1110  bottom row + top-right
    "█",            # 0b1111  full
]


def render_blocks(grid: list[list[int]]) -> list[str]:
    """Reduce a binary grid to ~half-height unicode block rows."""
    h = len(grid)
    rows: list[str] = []
    for y in range(0, h, 2):
        top = grid[y]
        bot = grid[y + 1] if y + 1 < h else [0] * len(grid[0])
        row = []
        for x in range(0, len(top), 2):
            tl, tr = top[x], top[x + 1] if x + 1 < len(top) else 0
            bl, br = bot[x], bot[x + 1] if x + 1 < len(bot) else 0
            code = (bl << 3) | (br << 2) | (tl << 1) | tr
            row.append(_BLOCKS[code])
        rows.append("".join(row))
    return rows


def render_ansi(grid: list[list[int]]) -> str:
    """Render the whole grid as ANSI-coloured block rows."""
    out = []
    for row in render_blocks(grid):
        out.append("\033[36;1m" + row + "\033[0m")
    return "\n".join(out)

# ---------------------------------------------------------------------------
# Interactive curses mode
# ---------------------------------------------------------------------------


def CLEAR() -> str:
    return "\033[2J\033[H"


def run_interactive() -> None:
    import curses

    def main(stdscr) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        try:
            stdscr.keypad(True)
        except Exception:
            pass

        h, w = stdscr.getmaxyx()
        gh, gw = h - 4, w
        if gh < 8 or gw < 16:
            stdscr.addstr(0, 0, "Terminal too small. Resize and rerun.")
            stdscr.refresh()
            time.sleep(2)
            return

        rule_name = "life"
        preset_name = "random"
        grid = PRESETS[preset_name]["make"](gw, gh)

        frame = 0
        speed = 0.12
        running = True
        status = f"[critters] rule={rule_name} preset={preset_name} frame={frame}  "
        status += "[space] pause  [r] random  [g] glider  [p] pulsar  [n] next  [q] quit"

        while True:
            try:
                key = stdscr.getch()
            except Exception:
                key = -1

            if key == ord("q"):
                break
            elif key == ord(" "):
                running = not running
            elif key == ord("n"):
                running = False
                grid = step(grid, rule_name)
                frame += 1
            elif key == ord("r"):
                preset_name = "random"
                grid = PRESETS[preset_name]["make"](gw, gh)
                frame = 0
            elif key == ord("g"):
                preset_name = "glider"
                grid = PRESETS[preset_name]["make"](gw, gh)
                frame = 0
            elif key == ord("p"):
                preset_name = "pulsar"
                grid = PRESETS[preset_name]["make"](gw, gh)
                frame = 0

            if running:
                grid = step(grid, rule_name)
                frame += 1
                time.sleep(speed)

            stdscr.clear()
            try:
                for i, line in enumerate(render_blocks(grid)):
                    if i < gh:
                        stdscr.addstr(i, 0, line)
                stdscr.addstr(gh, 0, status)
            except curses.error:
                pass
            stdscr.refresh()

    curses.wrapper(main)


def step(grid, rule_name: str) -> list[list[int]]:
    return RULES[rule_name][0](grid)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="critters",
                                 description="Terminal cellular automata playground.")
    ap.add_argument("--preset", "-p", default="random",
                    choices=sorted(PRESETS), help="Initial pattern (default: random).")
    ap.add_argument("--rule", "-r", default="life",
                    choices=sorted(RULES), help="Automaton rule (default: life).")
    ap.add_argument("--frames", "-f", type=int, default=None,
                    help="Headless: number of frames to draw (default: 20 when not interactive).")
    ap.add_argument("--cols", type=int, default=80,
                    help="Headless grid width (default: 80).")
    ap.add_argument("--rows", type=int, default=48,
                    help="Headless grid height ( default: 48).")
    ap.add_argument("--delay", type=float, default=0.08,
                    help="Headless delay between frames in seconds (default: 0.08).")
    ap.add_argument("--list", action="store_true",
                    help="List available presets and rules, then exit.")
    args = ap.parse_args(argv)

    if args.list:
        print("Presets:")
        for name in sorted(PRESETS):
            print(f"  {name:<14} {PRESETS[name]['desc']}")
        print("\nRules:")
        for name in sorted(RULES):
            print(f"  {name:<14} {RULES[name][1]}")
        return 0

    if sys.stdout.isatty() and args.frames is None:
        run_interactive()
        return 0

    # Headless ANSI mode
    frames = args.frames if args.frames is not None else 20
    grid = PRESETS[args.preset]["make"](args.cols, args.rows)
    for f in range(frames):
        print(CLEAR(), end="")
        print(render_ansi(grid))
        print(f"\033[90mframe {f} | rule={args.rule} | preset={args.preset}\033[0m")
        grid = step(grid, args.rule)
        time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(130)
