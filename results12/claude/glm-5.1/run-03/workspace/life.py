#!/usr/bin/env python3
"""
✦ C O N W A Y ' S   G A M E   O F   L I F E ✦
─────────────────────────────────────────────────
A beautiful terminal-based cellular automaton simulator.

Rules:
  1. Any live cell with 2-3 neighbors survives
  2. Any dead cell with exactly 3 neighbors becomes alive
  3. All other cells die or stay dead

Controls:
  SPACE  - Pause/Resume
  N      - Next step (when paused)
  R      - Reset with random cells
  1-6    - Load preset pattern
  +/-    - Speed up / Slow down
  Q      - Quit
"""

import shutil
import sys
import time
import random
import signal

# ── Configuration ──────────────────────────────────────────────

DEAD  = 0
ALIVE = 1

# Unicode block characters for smooth rendering
GLYPHS = {
    DEAD:  "  ",
    ALIVE: "██",
}

# ANSI colors for live cells — cycles through a gradient
PALETTE = [
    "\033[38;5;82m",    # bright green
    "\033[38;5;46m",    # green
    "\033[38;5;48m",    # sea green
    "\033[38;5;50m",    # spring green
    "\033[38;5;85m",    # pale green
    "\033[38;5;228m",   # gold (rare cells get warm)
]

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
CYAN  = "\033[38;5;87m"
MAGENTA = "\033[38;5;198m"
YELLOW = "\033[38;5;220m"

# ── Patterns ───────────────────────────────────────────────────

PATTERNS = {
    1: ("Random Soup", None),  # special case: random fill
    2: ("Glider Gun", [
            "........................O...........",
            "......................O.O...........",
            "............OO......OO............OO",
            "...........O...O....OO............OO",
            "OO........O.....O...OO..............",
            "OO........O...O.OO....O.O...........",
            "..........O.....O.......O...........",
            "...........O...O....................",
            "............OO......................",
        ]),
    3: ("Pulsar", [
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
    4: ("Pentadecathlon", [
            "..O....O..",
            "OO.OOOO.OO",
            "..O....O..",
        ]),
    5: ("R-pentomino", [
            ".OO",
            "OO.",
            ".O.",
        ]),
    6: ("Diehard", [
            "......O.",
            "OO......",
            ".O...OOO",
        ]),
}


# ── Grid Logic ────────────────────────────────────────────────

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[DEAD] * width for _ in range(height)]
        self.generation = 0
        self.population = 0

    def clear(self):
        self.cells = [[DEAD] * self.width for _ in range(self.height)]
        self.generation = 0
        self.population = 0

    def randomize(self, density=0.25):
        self.clear()
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.cells[y][x] = ALIVE
                    self.population += 1

    def load_pattern(self, pattern_lines):
        self.clear()
        for y, line in enumerate(pattern_lines):
            for x, ch in enumerate(line):
                if ch == "O" and y < self.height and x < self.width:
                    # Center the pattern
                    oy = y + (self.height - len(pattern_lines)) // 2
                    ox = x + (self.width - len(line)) // 2
                    if 0 <= oy < self.height and 0 <= ox < self.width:
                        self.cells[oy][ox] = ALIVE
                        self.population += 1

    def count_neighbors(self, x, y):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny = (y + dy) % self.height
                nx = (x + dx) % self.width
                count += self.cells[ny][nx]
        return count

    def step(self):
        new = [[DEAD] * self.width for _ in range(self.height)]
        pop = 0
        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(x, y)
                if self.cells[y][x] == ALIVE:
                    if n in (2, 3):
                        new[y][x] = ALIVE
                        pop += 1
                else:
                    if n == 3:
                        new[y][x] = ALIVE
                        pop += 1
        self.cells = new
        self.generation += 1
        self.population = pop

    def is_stable(self, prev_pop):
        return self.population == prev_pop and self.population > 0


# ── Renderer ──────────────────────────────────────────────────

class Renderer:
    def __init__(self):
        self._hide_cursor()
        signal.signal(signal.SIGINT, self._restore)

    def _hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def _restore(self, signum, frame):
        self.show_cursor()
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        sys.exit(0)

    def clear_screen(self):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def render(self, grid, paused, speed_ms, pattern_name):
        # Move cursor to home position (avoid full clear for less flicker)
        sys.stdout.write("\033[H")

        cols, rows = shutil.get_terminal_size()
        info_line = (
            f"{BOLD}{CYAN}✦ GAME OF LIFE ✦{RESET}   "
            f"{DIM}gen:{RESET} {BOLD}{grid.generation:<6}{RESET}   "
            f"{DIM}pop:{RESET} {BOLD}{grid.population:<6}{RESET}   "
            f"{DIM}speed:{RESET} {BOLD}{speed_ms}ms{RESET}   "
            f"{DIM}pattern:{RESET} {BOLD}{pattern_name}{RESET}   "
            f"{'  ' + MAGENTA + '⏸ PAUSED' + RESET if paused else ''}"
        )
        sys.stdout.write(info_line.ljust(cols) + "\n")

        # Separator
        sys.stdout.write(f"{DIM}{'─' * min(cols, grid.width * 2 + 2)}{RESET}\n")

        for y in range(grid.height):
            row = ""
            for x in range(grid.width):
                cell = grid.cells[y][x]
                if cell == ALIVE:
                    # Color based on neighbor count for visual variety
                    n = grid.count_neighbors(x, y)
                    color = PALETTE[min(n, len(PALETTE) - 1)]
                    row += color + GLYPHS[ALIVE] + RESET
                else:
                    row += GLYPHS[DEAD]
            sys.stdout.write(row + "\n")

        # Controls help
        sys.stdout.write(
            f"\n{DIM}[SPACE] Pause  [N] Step  [R] Random  "
            f"[1-6] Pattern  [+/-] Speed  [Q] Quit{RESET}\n"
        )
        sys.stdout.flush()


# ── Main Loop ─────────────────────────────────────────────────

def main():
    renderer = Renderer()

    # Determine grid size from terminal (leave room for UI)
    cols, rows = shutil.get_terminal_size()
    grid_w = (cols - 2) // 2   # each cell is 2 chars wide
    grid_h = rows - 4          # room for header + controls

    if grid_w < 10 or grid_h < 10:
        print("Terminal too small! Need at least 24x14.")
        sys.exit(1)

    grid = Grid(grid_w, grid_h)
    grid.randomize()
    pattern_name = "Random Soup"

    renderer.clear_screen()

    paused = False
    speed_ms = 80
    prev_pop = -1

    # Non-blocking keyboard input
    import select
    import tty
    import termios

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            # Render
            renderer.render(grid, paused, speed_ms, pattern_name)

            # Handle input
            while select.select([sys.stdin], [], [], 0.02 if not paused else 0.1)[0]:
                ch = sys.stdin.read(1)

                if ch == 'q' or ch == 'Q':
                    renderer.clear_screen()
                    print(f"\n  {BOLD}{CYAN}Thanks for watching life unfold!{RESET}\n")
                    return

                elif ch == ' ':
                    paused = not paused

                elif ch == 'n' or ch == 'N':
                    if paused:
                        prev_pop = grid.population
                        grid.step()

                elif ch == 'r' or ch == 'R':
                    grid.randomize()
                    pattern_name = "Random Soup"

                elif ch in '123456':
                    key = int(ch)
                    name, pattern = PATTERNS[key]
                    grid.clear()
                    if pattern is None:
                        grid.randomize()
                    else:
                        grid.load_pattern(pattern)
                    pattern_name = name

                elif ch == '+' or ch == '=':
                    speed_ms = max(10, speed_ms - 20)

                elif ch == '-' or ch == '_':
                    speed_ms = min(500, speed_ms + 20)

            # Step if not paused
            if not paused:
                prev_pop = grid.population
                grid.step()
                time.sleep(speed_ms / 1000.0)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        renderer.show_cursor()


if __name__ == "__main__":
    main()
