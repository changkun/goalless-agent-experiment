#!/usr/bin/env python3
"""
Conway's Game of Life — Colorful Terminal Edition
==================================================

Controls:
  Space   — Pause / Resume
  r       — Randomize grid
  c       — Clear grid
  1-5     — Load preset patterns (glider, pulsar, spaceship, etc.)
  p       — Place pattern mode (click with arrow keys + Enter)
  q / Esc — Quit
  +/-     — Speed up / slow down
  Mouse   — Click to toggle cells (if supported)

Rules:
  1. Any live cell with 2 or 3 neighbors survives.
  2. Any dead cell with exactly 3 neighbors becomes alive.
  3. All other cells die or stay dead.
"""

import curses
import time
import random
import argparse
from collections import namedtuple

# ── Patterns ──────────────────────────────────────────────────────────

PATTERNS = {
    "glider": [
        (0, 1), (1, 2), (2, 0), (2, 1), (2, 2),
    ],
    "lightweight_spaceship": [
        (0, 1), (0, 4),
        (1, 0),
        (2, 0), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 3),
    ],
    "pulsar": [
        (2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12),
        (4, 2), (4, 7), (4, 9), (4, 14),
        (5, 2), (5, 7), (5, 9), (5, 14),
        (6, 2), (6, 7), (6, 9), (6, 14),
        (7, 4), (7, 5), (7, 6), (7, 10), (7, 11), (7, 12),
        (9, 4), (9, 5), (9, 6), (9, 10), (9, 11), (9, 12),
        (10, 2), (10, 7), (10, 9), (10, 14),
        (11, 2), (11, 7), (11, 9), (11, 14),
        (12, 2), (12, 7), (12, 9), (12, 14),
        (14, 4), (14, 5), (14, 6), (14, 10), (14, 11), (14, 12),
    ],
    "gosper_glider_gun": [
        (5, 1), (5, 2), (6, 1), (6, 2),
        (5, 11), (6, 11), (7, 11),
        (4, 12), (8, 12),
        (3, 13), (9, 13),
        (3, 14), (9, 14),
        (6, 15),
        (4, 16), (8, 16),
        (5, 17), (6, 17), (7, 17),
        (6, 18),
        (3, 21), (4, 21), (5, 21),
        (3, 22), (4, 22), (5, 22),
        (2, 23), (6, 23),
        (1, 25), (2, 25), (6, 25), (7, 25),
        (3, 35), (4, 35),
        (3, 36), (4, 36),
    ],
    "diehard": [
        (5, 6), (6, 0), (6, 1), (7, 1), (7, 5), (7, 6), (7, 7),
    ],
    "acorn": [
        (4, 5), (5, 5), (5, 7), (6, 4), (7, 5), (8, 5), (8, 5),
        (6, 4), (7, 5), (4, 5), (5, 5), (5, 7), (7, 4), (8, 5),
    ],
    # Cleaned-up acorn:
    "r_pentomino": [
        (0, 1), (0, 2), (1, 0), (1, 1), (2, 1),
    ],
}

# Clean up acorn duplicate entries
PATTERNS["acorn"] = [
    (4, 5), (5, 5), (5, 7), (6, 4), (7, 5), (8, 5), (7, 4),
]

# ── Color palette for cells by age ────────────────────────────────────

def make_palette():
    """Build a palette mapping age → curses color pair index."""
    pairs = {}
    for i in range(1, 61):
        # Hue cycles from green (young) → cyan → blue → magenta → red (old)
        hue = (i - 1) / 59.0
        r = int(1000 * min(hue * 2, 1.0))
        g = int(1000 * max(0, 1.0 - abs(hue - 0.33) * 3))
        b = int(1000 * max(0, 1.0 - abs(hue - 0.66) * 3))
        pairs[i] = (r, g, b)
    return pairs

CELL_PALETTE = make_palette()

# ── Game engine ───────────────────────────────────────────────────────

class GameOfLife:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.age = [[0 for _ in range(cols)] for _ in range(rows)]
        self.generation = 0
        self.population = 0
        self.running = True
        self.delay = 0.08  # seconds per tick

    def clear(self):
        """Reset the grid."""
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.age = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.generation = 0
        self.population = 0

    def randomize(self, density=0.3):
        """Fill grid with random cells."""
        self.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                if random.random() < density:
                    self.grid[r][c] = 1
                    self.age[r][c] = 1
                    self.population += 1

    def place_pattern(self, name, row_offset=None, col_offset=None):
        """Place a named pattern centered in the grid."""
        if name not in PATTERNS:
            return False
        cells = PATTERNS[name]
        coords = set(cells)
        if row_offset is None:
            min_r = min(r for r, _ in coords)
            max_r = max(r for r, _ in coords)
            row_offset = self.rows // 2 - (max_r - min_r) // 2
        if col_offset is None:
            min_c = min(c for _, c in coords)
            max_c = max(c for _, c in coords)
            col_offset = self.cols // 2 - (max_c - min_c) // 2

        for r, c in coords:
            rr, cc = r + row_offset, c + col_offset
            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                self.grid[rr][cc] = 1
                self.age[rr][cc] = 1
                self.population += 1
        return True

    def toggle_cell(self, row, col):
        """Flip a cell alive/dead."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if self.grid[row][col]:
                self.grid[row][col] = 0
                self.age[row][col] = 0
                self.population -= 1
            else:
                self.grid[row][col] = 1
                self.age[row][col] = 1
                self.population += 1

    def tick(self):
        """Advance one generation."""
        new_grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        new_age = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        new_pop = 0

        for r in range(self.rows):
            for c in range(self.cols):
                # Count live neighbors (toroidal)
                neighbors = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr = (r + dr) % self.rows
                        nc = (c + dc) % self.cols
                        neighbors += self.grid[nr][nc]

                if self.grid[r][c] == 1:
                    if neighbors in (2, 3):
                        new_grid[r][c] = 1
                        new_age[r][c] = self.age[r][c] + 1
                        new_pop += 1
                else:
                    if neighbors == 3:
                        new_grid[r][c] = 1
                        new_age[r][c] = 1
                        new_pop += 1

        self.grid = new_grid
        self.age = new_age
        self.population = new_pop
        self.generation += 1

# ── Curses UI ─────────────────────────────────────────────────────────

def clamp_age_for_color(age):
    """Map age to a color index. Ages 1–60 get distinct colors; beyond that cycles."""
    if age <= 0:
        return 0
    return 1 + ((age - 1) % 60)


def draw(stdscr, game):
    """Full render of the game state."""
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    # Calculate cell dimensions — leave room for status bar
    game_h = h - 2  # reserve bottom 2 lines for status
    game_w = w

    cell_h = max(1, game_h // game.rows)
    cell_w = max(1, game_w // game.cols)

    # Use 2 chars per cell for a more square-ish look (terminal chars are tall)
    cell_w = max(2, cell_w)

    # Draw cells
    for r in range(game.rows):
        row_y = r * cell_h
        if row_y >= game_h:
            break
        for c in range(game.cols):
            col_x = c * cell_w
            if col_x >= game_w - 1:
                break

            age = game.age[r][c]
            if age > 0:
                color_idx = clamp_age_for_color(age)
                try:
                    stdscr.addstr(row_y, col_x, "█" * cell_w,
                                  curses.color_pair(color_idx))
                except curses.error:
                    pass  # bottom-right corner write
            else:
                # Draw grid dots for empty cells
                try:
                    stdscr.addstr(row_y, col_x, "·" * cell_w,
                                  curses.color_pair(0) | curses.A_DIM)
                except curses.error:
                    pass

    # ── Status bar ──────────────────────────────────────────────────
    status_y = h - 2
    status = (
        f" Gen: {game.generation:,}  "
        f"Pop: {game.population:,}  "
        f"Speed: {game.delay:.3f}s  "
        f"{'▶ RUNNING' if game.running else '⏸  PAUSED'}  "
        f"[Space:pause r:random c:clear 1-5:patterns p:place +:faster -:slower q:quit]"
    )

    # Truncate status if too wide
    if len(status) > w - 1:
        status = status[:w - 2]

    try:
        stdscr.addstr(status_y, 0, status[:w - 1], curses.A_REVERSE)
    except curses.error:
        pass

    # Help bar
    help_y = h - 1
    help_text = (
        "1:Glider  2:LWSS  3:Pulsar  4:GosperGun  5:Diehard  6:R-pentomino  7:Acorn"
    )
    try:
        stdscr.addstr(help_y, 0, help_text[:w - 1],
                      curses.color_pair(0))
    except curses.error:
        pass

    stdscr.refresh()


def init_colors():
    """Set up color pairs for cell ages."""
    curses.start_color()
    curses.use_default_colors()

    # Color pair 0: default (dim dots)
    curses.init_pair(0, 8, -1)  # grey on default bg

    for age, (r, g, b) in CELL_PALETTE.items():
        try:
            # curses can_init_color returns True if supported
            if curses.can_change_color():
                color_idx = 16 + age  # use colors beyond the 16 base colors
                if color_idx < curses.COLORS:
                    curses.init_color(color_idx, r, g, b)
                    curses.init_pair(age, color_idx, -1)
        except curses.error:
            # Fallback: use the 8 standard colors
            curses.init_pair(age, (age % 7) + 1, -1)


def placement_mode(stdscr, game):
    """Interactive pattern placement with arrow keys."""
    h, w = stdscr.getmaxyx()
    game_h = h - 2
    game_w = w

    cell_h = max(1, game_h // game.rows)
    cell_w = max(2, game_w // game.cols)

    cur_r = game.rows // 2
    cur_c = game.cols // 2

    while True:
        # Draw with cursor highlight
        draw(stdscr, game)
        cur_y = cur_r * cell_h
        cur_x = cur_c * cell_w
        for i in range(cell_h):
            try:
                stdscr.addstr(cur_y + i, cur_x, "▓" * cell_w, curses.A_REVERSE)
            except curses.error:
                pass

        msg = f" Placement mode — Row:{cur_r} Col:{cur_c}  [Arrows:move Enter:place p/Esc:cancel]"
        try:
            stdscr.addstr(h - 1, 0, msg[:w - 1], curses.A_BOLD)
        except curses.error:
            pass
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('p'), 27):  # p or Esc
            break
        elif key == curses.KEY_UP and cur_r > 0:
            cur_r -= 1
        elif key == curses.KEY_DOWN and cur_r < game.rows - 1:
            cur_r += 1
        elif key == curses.KEY_LEFT and cur_c > 0:
            cur_c -= 1
        elif key == curses.KEY_RIGHT and cur_c < game.cols - 1:
            cur_c += 1
        elif key in (10, 13, ord(' ')):  # Enter or Space
            game.toggle_cell(cur_r, cur_c)


def main(stdscr, args):
    # Initialise
    curses.curs_set(0)  # hide cursor
    stdscr.nodelay(True)  # non-blocking getch
    stdscr.timeout(50)   # ms timeout for getch

    # Mouse support
    try:
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        mouse_supported = True
    except curses.error:
        mouse_supported = False

    init_colors()

    # Calculate grid dimensions from terminal size
    h, w = stdscr.getmaxyx()
    game_h = h - 2
    game_w = w
    cell_w = max(2, game_w // max(1, args.cols or 80))
    cell_h = max(1, game_h // max(1, args.rows or 40))

    rows = args.rows or max(10, game_h // cell_h)
    cols = args.cols or max(10, game_w // cell_w)

    game = GameOfLife(rows, cols)

    # Initial pattern
    if args.pattern:
        game.place_pattern(args.pattern)
    elif args.random:
        game.randomize(args.density)
    else:
        # Default: glider in the middle
        game.place_pattern("glider")
        # Add a few more for visual interest
        game.place_pattern("glider", row_offset=rows // 4, col_offset=cols // 4)
        game.place_pattern("lightweight_spaceship", row_offset=rows // 3, col_offset=cols * 3 // 4)

    last_tick = time.time()

    while True:
        # Handle input
        key = stdscr.getch()

        if key == ord('q') or key == 27:  # q or Esc
            break
        elif key == ord(' '):
            game.running = not game.running
        elif key == ord('r'):
            game.randomize(args.density)
        elif key == ord('c'):
            game.clear()
        elif key == ord('+') or key == ord('='):
            game.delay = max(0.005, game.delay * 0.75)
        elif key == ord('-') or key == ord('_'):
            game.delay = min(1.0, game.delay * 1.33)
        elif key == ord('p'):
            game.running = False
            placement_mode(stdscr, game)
        # Number keys for patterns
        elif key == ord('1'):
            game.place_pattern("glider")
        elif key == ord('2'):
            game.place_pattern("lightweight_spaceship")
        elif key == ord('3'):
            game.place_pattern("pulsar")
        elif key == ord('4'):
            game.place_pattern("gosper_glider_gun")
        elif key == ord('5'):
            game.place_pattern("diehard")
        elif key == ord('6'):
            game.place_pattern("r_pentomino")
        elif key == ord('7'):
            game.place_pattern("acorn")
        # Mouse click to toggle cells
        elif key == curses.KEY_MOUSE and mouse_supported:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON1_CLICKED:
                    cell_h_actual = max(1, game_h // game.rows)
                    cell_w_actual = max(2, game_w // game.cols)
                    clicked_r = my // cell_h_actual
                    clicked_c = mx // cell_w_actual
                    if 0 <= clicked_r < game.rows and 0 <= clicked_c < game.cols:
                        game.toggle_cell(clicked_r, clicked_c)
                        draw(stdscr, game)  # immediate feedback
            except curses.error:
                pass
        # Resize handling
        elif key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            stdscr.clear()
            draw(stdscr, game)

        # Tick if running
        if game.running:
            now = time.time()
            if now - last_tick >= game.delay:
                game.tick()
                last_tick = now

        draw(stdscr, game)

        # Small sleep to avoid busy-waiting
        time.sleep(0.01)


def parse_args():
    p = argparse.ArgumentParser(
        description="Conway's Game of Life — Colorful Terminal Edition"
    )
    p.add_argument("-r", "--rows", type=int, default=0,
                   help="Grid rows (default: auto-fit terminal)")
    p.add_argument("-c", "--cols", type=int, default=0,
                   help="Grid columns (default: auto-fit terminal)")
    p.add_argument("-p", "--pattern", choices=list(PATTERNS.keys()),
                   help="Initial pattern to load")
    p.add_argument("--random", action="store_true",
                   help="Start with random grid")
    p.add_argument("-d", "--density", type=float, default=0.3,
                   help="Density for random grid (0-1, default: 0.3)")
    p.add_argument("--delay", type=float, default=0.08,
                   help="Initial tick delay in seconds (default: 0.08)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    curses.wrapper(main, args)
