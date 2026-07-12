#!/usr/bin/env python3
"""
Conway's Game of Life — terminal edition.

Controls:
  SPACE   pause / resume
  N       step forward one generation (while paused)
  R       reset with a new random seed
  1-6     load a preset pattern
  C       clear the board
  .       toggle cell under cursor (while paused)
  arrows  move cursor (while paused)
  Q       quit

Cell colors reflect age: newborn cells are bright green, aging through
yellow to red. Dead cells are dim dots.
"""

import curses
import random
import time
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Simulation core
# ---------------------------------------------------------------------------

ALIVE = 1
DEAD = 0


@dataclass
class Grid:
    """Toroidal grid where edges wrap around."""
    rows: int
    cols: int
    cells: list[list[int]] = field(default=None)
    age: list[list[int]] = field(default=None)  # generations a cell has been alive

    def __post_init__(self):
        if self.cells is None:
            self.cells = [[DEAD] * self.cols for _ in range(self.rows)]
        if self.age is None:
            self.age = [[0] * self.cols for _ in range(self.rows)]

    def neighbors(self, r: int, c: int) -> int:
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = (r + dr) % self.rows, (c + dc) % self.cols
                if self.cells[nr][nc] == ALIVE:
                    count += 1
        return count

    def step(self):
        """Advance one generation using the standard B3/S23 rules."""
        new_cells = [[DEAD] * self.cols for _ in range(self.rows)]
        new_age = [[0] * self.cols for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                n = self.neighbors(r, c)
                alive = self.cells[r][c] == ALIVE
                if alive and n in (2, 3):
                    new_cells[r][c] = ALIVE
                    new_age[r][c] = self.age[r][c] + 1
                elif not alive and n == 3:
                    new_cells[r][c] = ALIVE
                    new_age[r][c] = 1
        self.cells = new_cells
        self.age = new_age

    def population(self) -> int:
        return sum(cell for row in self.cells for cell in row)

    def clear(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c] = DEAD
                self.age[r][c] = 0

    def place(self, pattern: list[tuple[int, int]], origin_r: int = 0, origin_c: int = 0):
        """Stamp a pattern (list of (row, col) offsets) onto the grid."""
        for dr, dc in pattern:
            r, c = (origin_r + dr) % self.rows, (origin_c + dc) % self.cols
            self.cells[r][c] = ALIVE
            self.age[r][c] = 1


# ---------------------------------------------------------------------------
# Preset patterns — offsets relative to (0,0)
# ---------------------------------------------------------------------------

def glider() -> list[tuple[int, int]]:
    return [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]


def blinker() -> list[tuple[int, int]]:
    return [(0, 0), (0, 1), (0, 2)]


def pulsar() -> list[tuple[int, int]]:
    # A period-3 oscillator — one of the most elegant patterns.
    pts = []
    offsets = [
        (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
        (2, 0), (3, 0), (4, 0), (2, 5), (3, 5), (4, 5),
        (2, 7), (3, 7), (4, 7), (2, 12), (3, 12), (4, 12),
        (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
    ]
    for r, c in offsets:
        pts.append((r, c))
        pts.append((12 - r, c))  # mirror vertically
    return list(set(pts))


def gosper_glider_gun() -> list[tuple[int, int]]:
    """The famous period-30 glider gun discovered by Bill Gosper in 1970."""
    return [
        (0,24),(1,22),(1,24),(2,12),(2,13),(2,20),(2,21),(2,34),(2,35),
        (3,11),(3,15),(3,20),(3,21),(3,34),(3,35),(4,0),(4,1),(4,10),
        (4,16),(4,20),(4,21),(5,0),(5,1),(5,10),(5,14),(5,16),(5,17),
        (5,22),(5,24),(6,10),(6,16),(6,24),(7,11),(7,15),(8,12),(8,13),
    ]


def lwss() -> list[tuple[int, int]]:
    """Lightweight spaceship — moves horizontally."""
    return [(0,1),(0,4),(1,0),(2,0),(2,4),(3,0),(3,1),(3,2),(3,3)]


def random_soup(rows: int, cols: int, density: float = 0.25) -> list[tuple[int, int]]:
    pts = []
    for r in range(rows):
        for c in range(cols):
            if random.random() < density:
                pts.append((r, c))
    return pts


PRESETS = {
    "1": ("Glider swarm", lambda g: _place_gliders(g)),
    "2": ("Pulsar", lambda g: g.place(pulsar(), g.rows // 2 - 6, g.cols // 2 - 6)),
    "3": ("Gosper Glider Gun", lambda g: g.place(gosper_glider_gun(), 2, 2)),
    "4": ("LWSS fleet", lambda g: _place_lwss(g)),
    "5": ("Blinker row", lambda g: [g.place(blinker(), r, g.cols // 2 - 1) for r in range(2, g.rows - 2, 4)]),
    "6": ("Random soup", lambda g: g.place(random_soup(g.rows, g.cols, 0.2))),
}


def _place_gliders(g: Grid):
    for r in range(0, g.rows - 3, 6):
        for c in range(0, g.cols - 3, 8):
            g.place(glider(), r, c)


def _place_lwss(g: Grid):
    for r in range(2, g.rows - 5, 6):
        g.place(lwss(), r, 2)

# ---------------------------------------------------------------------------
# Color mapping — cell age → color pair id
# ---------------------------------------------------------------------------

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    # pair id: (fg, bg)
    pairs = [
        (1, curses.COLOR_GREEN, -1),    # newborn
        (2, curses.COLOR_CYAN, -1),     # young
        (3, curses.COLOR_YELLOW, -1),   # middle-aged
        (4, curses.COLOR_RED, -1),      # old
        (5, curses.COLOR_MAGENTA, -1),  # ancient
        (6, curses.COLOR_WHITE, curses.COLOR_BLACK),  # UI text
        (7, curses.COLOR_BLACK, curses.COLOR_GREEN),  # highlight
    ]
    for pid, fg, bg in pairs:
        curses.init_pair(pid, fg, bg)


def age_to_color(age: int) -> int:
    if age <= 1:
        return curses.color_pair(1)
    if age <= 3:
        return curses.color_pair(2)
    if age <= 8:
        return curses.color_pair(3)
    if age <= 20:
        return curses.color_pair(4)
    return curses.color_pair(5)

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

CELL_ALIVE = "██"
CELL_DEAD = "··"
LEGEND = "SPACE pause | N step | R reset | 1-6 presets | C clear | Q quit"


def draw(stdscr, grid: Grid, gen: int, paused: bool, pattern_name: str,
         cursor_r: int = 0, cursor_c: int = 0, show_cursor: bool = False):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    # Title bar
    title = f" Conway's Game of Life  │  gen {gen:>6}  │  pop {grid.population():>5}  │  {pattern_name} "
    if paused:
        title += " ⏸ PAUSED "
    title = title[:max_x - 1]
    try:
        stdscr.addstr(0, 0, title, curses.color_pair(6) | curses.A_BOLD)
    except curses.error:
        pass

    # Grid area: each cell is 2 chars wide, starts at row 2
    grid_top = 2
    grid_rows = min(grid.rows, max_y - grid_top - 2)
    grid_cols = min(grid.cols, (max_x) // 2)

    for r in range(grid_rows):
        line = ""
        attrs_list = []
        for c in range(grid_cols):
            if grid.cells[r][c] == ALIVE:
                line += CELL_ALIVE
                attrs_list.append(age_to_color(grid.age[r][c]))
            else:
                line += CELL_DEAD
                attrs_list.append(curses.A_DIM)

        y = grid_top + r
        if y >= max_y - 1:
            break
        try:
            # Write in chunks of 2 chars (one cell) for color accuracy
            x = 0
            for c in range(grid_cols):
                attr = attrs_list[c]
                cell_str = line[c*2:c*2+2]
                # Highlight cursor
                if show_cursor and r == cursor_r and c == cursor_c and paused:
                    attr = curses.color_pair(7) | curses.A_BOLD
                stdscr.addstr(y, x, cell_str, attr)
                x += 2
        except curses.error:
            pass

    # Status bar at bottom
    status = f" {LEGEND}"[:max_x - 1]
    try:
        stdscr.addstr(max_y - 1, 0, status, curses.color_pair(6) | curses.A_DIM)
    except curses.error:
        pass

    stdscr.refresh()

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(80)  # ~12 fps target
    init_colors()

    max_y, max_x = stdscr.getmaxyx()
    # Grid dimensions: use available space (2 chars per cell width)
    grid_rows = max(10, max_y - 4)
    grid_cols = max(20, (max_x) // 2)

    grid = Grid(grid_rows, grid_cols)
    gen = 0
    paused = False
    pattern_name = "Random soup"
    grid.place(random_soup(grid_rows, grid_cols, 0.2))

    cursor_r, cursor_c = 0, 0
    show_cursor = False
    last_time = time.time()
    target_fps = 12

    while True:
        # Input handling
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord(" "):
            paused = not paused
            show_cursor = paused
        elif key == ord("n") or key == ord("N"):
            if paused:
                grid.step()
                gen += 1
        elif key == ord("r") or key == ord("R"):
            grid.clear()
            gen = 0
            grid.place(random_soup(grid_rows, grid_cols, 0.2))
            pattern_name = "Random soup"
        elif key == ord("c") or key == ord("C"):
            grid.clear()
            gen = 0
            pattern_name = "Empty"
        elif key == ord("."):
            if paused:
                if grid.cells[cursor_r][cursor_c] == ALIVE:
                    grid.cells[cursor_r][cursor_c] = DEAD
                    grid.age[cursor_r][cursor_c] = 0
                else:
                    grid.cells[cursor_r][cursor_c] = ALIVE
                    grid.age[cursor_r][cursor_c] = 1
        elif key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            if paused:
                if key == curses.KEY_UP:
                    cursor_r = (cursor_r - 1) % grid_rows
                elif key == curses.KEY_DOWN:
                    cursor_r = (cursor_r + 1) % grid_rows
                elif key == curses.KEY_LEFT:
                    cursor_c = (cursor_c - 1) % grid_cols
                elif key == curses.KEY_RIGHT:
                    cursor_c = (cursor_c + 1) % grid_cols
                show_cursor = True
        elif chr(key) if 0 <= key < 256 else "" in PRESETS:
            ch = chr(key) if 0 <= key < 256 else ""
            if ch in PRESETS:
                grid.clear()
                gen = 0
                name, placer = PRESETS[ch]
                placer(grid)
                pattern_name = name

        # Simulation step (if running)
        now = time.time()
        if not paused and (now - last_time) >= (1.0 / target_fps):
            grid.step()
            gen += 1
            last_time = now

        # Render
        draw(stdscr, grid, gen, paused, pattern_name, cursor_r, cursor_c, show_cursor)


if __name__ == "__main__":
    curses.wrapper(main)
