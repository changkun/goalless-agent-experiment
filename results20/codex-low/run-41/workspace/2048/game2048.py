"""Terminal 2048 — a pure-Python, no-dependency clone.

Controls (arrow keys or WASD):
    Left / a   - slide tiles left  (merge)
    Right / d  - slide right
    Up / w     - slide up
    Down / s   - slide down
    q          - quit
    r          - restart
"""
import random
import sys

SIZE = 4
GOAL = 2048


class Game:
    def __init__(self, size: int = SIZE, goal: int = GOAL, seed=None):
        self.size = size
        self.goal = goal
        self.rng = random.Random(seed)
        self.grid = [[0] * size for _ in range(size)]
        self.score = 0
        self.best = 0
        self.game_over = False
        self.won = False
        self._spawn()
        self._spawn()

    # --- tile helpers -----------------------------------------------------
    def _free_cells(self):
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] == 0
        ]

    def _spawn(self) -> bool:
        cells = self._free_cells()
        if not cells:
            return False
        r, c = self.rng.choice(cells)
        self.grid[r][c] = 2 if self.rng.random() < 0.9 else 4
        return True

    # --- move logic --------------------------------------------------------
    @staticmethod
    def _slide_row(row):
        """Compress+merge one row toward index 0. Returns (new_row, gained)."""
        tiles = [v for v in row if v != 0]
        merged = []
        gained = 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                val = tiles[i] * 2
                merged.append(val)
                gained += val
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (len(row) - len(merged))
        return merged, gained

    def _transpose(self, grid):
        return [list(col) for col in zip(*grid)]

    def move(self, direction: str) -> bool:
        """direction in {'left','right','up','down'}.
        Returns True if the board changed."""
        if self.game_over:
            return False

        before = [row[:] for row in self.grid]
        gained_total = 0

        if direction == "left":
            lines = [Game._slide_row(row) for row in self.grid]
            self.grid = [l for l, _ in lines]
            gained_total = sum(g for _, g in lines)
        elif direction == "right":
            lines = []
            for row in self.grid:
                rev, g = Game._slide_row(list(reversed(row)))
                rev = list(reversed(rev))
                lines.append((rev, g))
            self.grid = [l for l, _ in lines]
            gained_total = sum(g for _, g in lines)
        elif direction == "up":
            t = self._transpose(self.grid)
            lines = [Game._slide_row(row) for row in t]
            t = [l for l, _ in lines]
            self.grid = self._transpose(t)
            gained_total = sum(g for _, g in lines)
        elif direction == "down":
            t = self._transpose(self.grid)
            lines = []
            for row in t:
                rev, g = Game._slide_row(list(reversed(row)))
                rev = list(reversed(rev))
                lines.append((rev, g))
            t = [l for l, _ in lines]
            self.grid = self._transpose(t)
            gained_total = sum(g for _, g in lines)
        else:
            raise ValueError(f"unknown direction: {direction}")

        changed = self.grid != before
        if changed:
            self.score += gained_total
            self.best = max(self.best, self.score)
            self._spawn()
            if not self.won and any(
                self.grid[r][c] >= self.goal
                for r in range(self.size)
                for c in range(self.size)
            ):
                self.won = True
            self.game_over = not self._moves_available()
        return changed

    def _moves_available(self) -> bool:
        if self._free_cells():
            return True
        for r in range(self.size):
            for c in range(self.size):
                val = self.grid[r][c]
                if c + 1 < self.size and self.grid[r][c + 1] == val:
                    return True
                if r + 1 < self.size and self.grid[r + 1][c] == val:
                    return True
        return False

    # --- UI helpers -------------------------------------------------------
    def state(self):
        return {
            "grid": [row[:] for row in self.grid],
            "score": self.score,
            "best": self.best,
            "won": self.won,
            "game_over": self.game_over,
            "goal": self.goal,
        }


# --- terminal rendering ---------------------------------------------------
TILE_COLORS = {
    0: "\033[48;5;236m",
    2: "\033[48;5;233m",
    4: "\033[48;5;234m",
    8: "\033[48;5;94m",
    16: "\033[48;5;130m",
    32: "\033[48;5;166m",
    64: "\033[48;5;202m",
    128: "\033[48;5;178m",
    256: "\033[48;5;220m",
    512: "\033[48;5;226m",
    1024: "\033[48;5;214m",
    2048: "\033[48;5;196m",
}
RESET = "\033[0m"


def tile_color(value: int) -> str:
    if value > 2048:
        return "\033[48;5;201m"
    return TILE_COLORS.get(value, "\033[48;5;239m")


def render(game: Game) -> str:
    lines = []
    lines.append(
        f"  Score: {game.score}   Best: {game.best}   Goal: {game.goal}"
    )
    lines.append("")
    pad = max(1, len(str(game.goal)) + 1)
    for row in game.grid:
        parts = []
        for v in row:
            text = str(v) if v else "."
            parts.append(f"{tile_color(v)} {text:>{pad}}{RESET}")
        lines.append("  " + " ".join(parts))
    lines.append("")
    if game.won and not game.game_over:
        lines.append("  🎉 You reached the goal! Keep going or press r to restart.")
    if game.game_over:
        lines.append("  💀 Game over — no moves left. Press r to restart or q to quit.")
    return "\n".join(lines)


def get_action(ch: str) -> str | None:
    mapping = {
        "\x1b[A": "up",
        "w": "up",
        "W": "up",
        "\x1b[B": "down",
        "s": "down",
        "S": "down",
        "\x1b[C": "right",
        "d": "right",
        "D": "right",
        "\x1b[D": "left",
        "a": "left",
        "A": "left",
    }
    return mapping.get(ch)


# --- main loop ------------------------------------------------------------
def play_loop(game: Game):
    import os
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            os.system("clear")
            sys.stdout.write(render(game))
            sys.stdout.write(
                "\n  [arrows/WASD] move  [r] restart  [q] quit\n\n  "
            )
            sys.stdout.flush()

            while True:
                if not select.select([sys.stdin], [], [], 0.2)[0]:
                    # Poll game state so nothing blocks; ensures redraws stay live.
                    if game.game_over:
                        break
                    continue
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    # read rest of escape sequence
                    seq = ch + sys.stdin.read(1) + sys.stdin.read(1)
                    action = get_action(seq)
                elif ch in "qrQR":
                    action = ch
                else:
                    action = get_action(ch)
                break

            if action in ("q", "Q"):
                break
            if action in ("r", "R"):
                game = Game(size=game.size, goal=game.goal)
                continue
            if action in (
                "up",
                "down",
                "left",
                "right",
            ):
                game.move(action)
                if game.game_over:
                    pass  # final message will display on next redraw
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print("\nThanks for playing! Final score:", game.score)


def main(argv):
    size = SIZE
    goal = GOAL
    seed = None
    args = iter(argv[1:])
    while True:
        try:
            arg = next(args)
        except StopIteration:
            break
        if arg in ("-h", "--help"):
            print(__doc__)
            return 0
        elif arg in ("--size", "-n"):
            size = int(next(args))
        elif arg in ("--goal", "-g"):
            goal = int(next(args))
        elif arg in ("--seed", "-s"):
            seed = int(next(args))
        else:
            print(f"unknown argument: {arg}", file=sys.stderr)
            return 2

    game = Game(size=size, goal=goal, seed=seed)
    play_loop(game)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
