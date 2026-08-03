#!/usr/bin/env python3
"""Terminal 2048 - a console implementation of the classic sliding-tile puzzle.

Move with WASD / arrow keys, 'u' to undo, 'r' to restart, 'q' to quit.
"""
import curses
import random
import sys

SIZE = 4
TARGET_TILE = 2048


class Board:
    """Holds the grid state and all game logic."""

    def __init__(self):
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.history = []          # stack of (grid, score) for undo
        self.best = 0
        self.new_tile = 0          # tile placed by the last move
        self._spawn()
        self._spawn()

    # -- grid math ---------------------------------------------------------
    def _spawn(self):
        empty = [(r, c) for r in range(SIZE) for c in range(SIZE)
                 if self.grid[r][c] == 0]
        if not empty:
            return
        r, c = random.choice(empty)
        self.grid[r][c] = 2 if random.random() < 0.9 else 4
        self.new_tile = self.grid[r][c]

    def _line_move(self, line):
        """Slide a single row/col left, merging equal neighbors."""
        tiles = [v for v in line if v != 0]
        merged = []
        i = 0
        gained = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                value = tiles[i] * 2
                merged.append(value)
                gained += value
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (SIZE - len(merged))
        return merged, gained

    def move(self, direction):
        """Direction in 'up', 'down', 'left', 'right'. Returns True if moved."""
        transient = self._extract(direction)
        moved = False
        gained = 0
        new_lines = []
        for line in transient:
            moved_line, g = self._line_move(list(line))
            gained += g
            new_lines.append(moved_line)
            if tuple(moved_line) != tuple(line):
                moved = True
        if not moved:
            return False
        self.history.append(([row[:] for row in self.grid], self.score))
        self._inject(direction, new_lines)
        self.score += gained
        self.best = max(self.best, self.score)
        self._spawn()
        return True

    def _extract(self, direction):
        """Return grid lines as row-lists depending on slide direction."""
        if direction == 'left':
            return [[self.grid[r][c] for c in range(SIZE)] for r in range(SIZE)]
        if direction == 'right':
            return [[self.grid[r][c] for c in range(SIZE - 1, -1, -1)]
                    for r in range(SIZE)]
        if direction == 'down':
            return [[self.grid[r][c] for r in range(SIZE - 1, -1, -1)]
                    for c in range(SIZE)]
        # up
        return [[self.grid[r][c] for r in range(SIZE)] for c in range(SIZE)]

    def _inject(self, direction, lines):
        if direction == 'left':
            for r in range(SIZE):
                for c in range(SIZE):
                    self.grid[r][c] = lines[r][c]
        elif direction == 'right':
            for r in range(SIZE):
                for c in range(SIZE):
                    self.grid[r][c] = lines[r][SIZE - 1 - c]
        elif direction == 'down':
            for c in range(SIZE):
                for r in range(SIZE):
                    self.grid[r][c] = lines[c][SIZE - 1 - r]
        else:  # up
            for c in range(SIZE):
                for r in range(SIZE):
                    self.grid[r][c] = lines[c][r]

    # -- game state --------------------------------------------------------
    def reset(self):
        """Start fresh but keep the all-time best score."""
        best = self.best
        self.__init__()
        self.best = best

    def undo(self):
        if not self.history:
            return False
        self.grid, self.score = self.history.pop()
        self.best = max(self.best, self.score)
        return True

    def has_won(self):
        return TARGET_TILE in (v for row in self.grid for v in row)

    def can_move(self):
        if any(0 in row for row in self.grid):
            return True
        for r in range(SIZE):
            for c in range(SIZE):
                v = self.grid[r][c]
                if (r + 1 < SIZE and self.grid[r + 1][c] == v) or \
                   (c + 1 < SIZE and self.grid[r][c + 1] == v):
                    return True
        return False

    # -- rendering helpers -------------------------------------------------
    def _cell_width(self):
        max_len = max(len(str(v)) for row in self.grid for v in row)
        default = len(str(TARGET_TILE))
        return max(max_len, default) + 2


class App:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board = Board()
        self.over = False
        self.won = False
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            self._init_colors()

    # -- colors ------------------------------------------------------------
    def _init_colors(self):
        self.colors = {}
        palette = {2: 236, 4: 238, 8: 240, 16: 94, 32: 166, 64: 202,
                   128: 208, 256: 214, 512: 220, 1024: 228, 2048: 231}
        for i, (value, color) in enumerate(palette.items()):
            curses.init_pair(i + 1, curses.COLOR_BLACK, color)
            self.colors[value] = curses.color_pair(i + 1)
        # default empty-cell color: dark gray background, gray text
        curses.init_pair(50, curses.COLOR_WHITE, 236)
        self.empty_color = curses.color_pair(50)

    # -- drawing -----------------------------------------------------------
    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        board = self.board
        cell = board._cell_width()

        title = "  TERMINAL 2048  "
        self._center(w, 0, title, curses.A_BOLD)
        status = f"Score: {board.score}   Best: {board.best}   "
        if board.history:
            status += f"Undos: {len(board.history)}"
        self._center(w, 2, status)

        # message area
        if self.over:
            msg = "GAME OVER - press 'r' to restart or 'q' to quit"
        elif self.won:
            msg = "YOU WIN! keep going or press 'r' to restart"
        elif self.board.new_tile:
            msg = ""
        else:
            msg = ""
        self._center(w, 3, msg)

        # grid
        total_w = SIZE * (cell + 1) + 1
        top = 5
        left = max(0, (w - total_w) // 2)
        self._box(left, top, total_w, SIZE * 2 + 1)

        for r in range(SIZE):
            y = top + 1 + r * 2
            for c in range(SIZE):
                v = board.grid[r][c]
                x = left + 1 + c * (cell + 1)
                text = str(v) if v else ""
                attr = self.colors.get(v, self.empty_color if not v else curses.A_NORMAL)
                pad = cell - len(text)
                lpad = pad // 2
                rpad = pad - lpad
                self.stdscr.addstr(y, x, " " * lpad)
                self.stdscr.addstr(y, x + lpad, text, attr)
                self.stdscr.addstr(y, x + lpad + len(text), " " * rpad)

        self._center(w, top + SIZE * 2 + 2,
                     "WASD/arrows: move   u: undo   r: restart   q: quit")

    def _box(self, left, top, width, height):
        self.stdscr.addstr(top, left, "+" + "-" * (width - 2) + "+")
        for y in range(top + 1, top + height - 1):
            self.stdscr.addstr(y, left, "|")
            self.stdscr.addstr(y, left + width - 1, "|")
        self.stdscr.addstr(top + height - 1, left,
                           "+" + "-" * (width - 2) + "+")

    def _center(self, width, y, text, attr=curses.A_NORMAL):
        x = max(0, (width - len(text)) // 2)
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    # -- main loop ---------------------------------------------------------
    def run(self):
        while True:
            self.draw()
            self.stdscr.refresh()

            if self.over or self.won:
                key = self.stdscr.getch()
                if key in (ord('r'), ord('R')):
                    self.board.reset()
                    self.over = False
                    self.won = False
                    continue
                if key in (ord('q'), ord('Q')):
                    return
                continue

            key = self.stdscr.getch()
            direction = None
            if key in (ord('w'), ord('W'), curses.KEY_UP):
                direction = 'up'
            elif key in (ord('s'), ord('S'), curses.KEY_DOWN):
                direction = 'down'
            elif key in (ord('a'), ord('A'), curses.KEY_LEFT):
                direction = 'left'
            elif key in (ord('d'), ord('D'), curses.KEY_RIGHT):
                direction = 'right'
            elif key in (ord('u'), ord('U')):
                if self.board.undo():
                    self.won = self.board.has_won()
                continue
            elif key in (ord('r'), ord('R')):
                self.board.reset()
                self.won = False
                continue
            elif key in (ord('q'), ord('Q')):
                return

            if direction:
                self.board.move(direction)
                self.won = self.board.has_won()
                if not self.board.can_move():
                    self.over = True


def main(stdscr):
    app = App(stdscr)
    app.run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
