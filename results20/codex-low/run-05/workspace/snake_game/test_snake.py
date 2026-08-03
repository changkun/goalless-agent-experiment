import sys
import types
import unittest

# Fake curses module so we can run without a real terminal.
curses = types.ModuleType("curses")


class _Curses:
    def curs_set(self, *a): pass
    def color_pair(self, n): return n
    def init_pair(self, *a): pass
    def start_color(self): pass
    def use_default_colors(self): pass
    def has_colors(self): return True
    error = Exception


curses.curs_set = lambda *a: None
curses.color_pair = _Curses().color_pair
curses.init_pair = lambda *a: None
curses.start_color = lambda: None
curses.use_default_colors = lambda: None
curses.has_colors = lambda: True
curses.error = Exception
for i, name in enumerate(["COLOR_BLACK", "COLOR_RED", "COLOR_GREEN",
                           "COLOR_YELLOW", "COLOR_BLUE", "COLOR_MAGENTA",
                           "COLOR_CYAN", "COLOR_WHITE"]):
    setattr(curses, name, i + 1)
curses.A_BOLD = 1
curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT = 1, 2, 3, 4
sys.modules["curses"] = curses

import snake  # noqa: E402


class FakeScr:
    """Minimal stand-in for the curses window used by Game."""
    def __init__(self, h=20, w=40):
        self.h, self.w = h, w
        self.key = -1
    def getmaxyx(self): return self.h, self.w
    def erase(self): pass
    def nodelay(self, v): pass
    def keypad(self, v): pass
    def border(self): pass
    def addstr(self, *a): pass
    def refresh(self): pass
    def getch(self): return self.key


class SnakeLogicTest(unittest.TestCase):
    def test_snake_moves_and_grows(self):
        scr = FakeScr()
        g = snake.Game(scr, "Normal")
        start_len = len(g.snake)
        # Force a food nowhere near the head so it won't eat on first step.
        g.food = (3, 3)
        g.step()  # moves right
        self.assertEqual(len(g.snake), start_len)  # no growth
        self.assertEqual(g.snake[0], (g.snake[1][0] + 1, g.snake[1][1]))

        g.food = (g.snake[0][0] + 1, g.snake[0][1])  # put food just ahead
        g.step()
        self.assertEqual(len(g.snake), start_len + 1)  # grew
        self.assertEqual(g.score, 1)

    def test_wall_collision_ends_game(self):
        scr = FakeScr()
        g = snake.Game(scr, "Normal")
        # Move head to the right wall.
        g.snake = [(g.cols - 2, 5), (g.cols - 3, 5)]
        g.direction = snake.Direction.RIGHT
        g.next_direction = snake.Direction.RIGHT
        g.food = (3, 3)
        g.step()
        self.assertTrue(g.over)

    def test_self_collision_ends_game(self):
        scr = FakeScr()
        g = snake.Game(scr, "Normal")
        g.snake = [
            (6, 5), (6, 6), (5, 6), (5, 5),  # head curls into its own body
        ]
        # Head at (6,5), move down into (6,6), a body cell that is not the tail.
        g.direction = snake.Direction.DOWN
        g.next_direction = snake.Direction.DOWN
        g.food = (2, 2)
        g.step()
        self.assertTrue(g.over)

    def test_cannot_reverse(self):
        scr = FakeScr()
        g = snake.Game(scr, "Normal")
        g.direction = snake.Direction.RIGHT
        g.handle_key(ord("a"))  # try to go left (opposite)
        self.assertEqual(g.next_direction, snake.Direction.RIGHT)


if __name__ == "__main__":
    unittest.main()
