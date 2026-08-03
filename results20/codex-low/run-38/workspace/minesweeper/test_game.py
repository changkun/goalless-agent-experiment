import random
import unittest

from .cli import Board, parse_command
from .game import Game


class GameLogicTest(unittest.TestCase):
    def test_board_dimensions(self):
        g = Game(width=5, height=4, mines=3)
        self.assertEqual(len(g.cells), 20)
        self.assertEqual(g.mines, 3)

    def test_mines_not_placed_before_first_action(self):
        g = Game(width=4, height=4, mines=2)
        self.assertFalse(any(c.mine for c in g.cells))

    def test_first_reveal_is_never_a_mine(self):
        for seed in range(50):
            g = Game(rng=random.Random(seed))
            g.reveal(0, 0)
            self.assertFalse(g.cells[0].mine)

    def test_flood_fill_reveals_empty_region(self):
        g = Game(width=3, height=3, mines=0)
        g.reveal(1, 1)
        self.assertTrue(all(c.revealed for c in g.cells))

    def test_flagged_cells_not_revealed(self):
        g = Game(width=4, height=4, mines=0)
        g.toggle_flag(1, 1)
        g.reveal(1, 1)
        self.assertFalse(g.cells[g.index(1, 1)].revealed)

    def test_flag_toggle(self):
        g = Game(width=4, height=4, mines=1)
        g.toggle_flag(0, 0)
        self.assertTrue(g.cells[0].flagged)
        g.toggle_flag(0, 0)
        self.assertFalse(g.cells[0].flagged)

    def test_flags_remaining(self):
        g = Game(width=4, height=4, mines=3)
        self.assertEqual(g.flags_remaining(), 3)
        g.toggle_flag(0, 0)
        g.toggle_flag(1, 1)
        self.assertEqual(g.flags_remaining(), 1)

    def test_adjacent_mine_count(self):
        g = Game(width=4, height=4, mines=8)
        for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            g.cells[g.index(1 + dx, 1 + dy)].mine = True
        g._place_mines = lambda: None  # avoid re-randomizing
        for x in range(4):
            for y in range(4):
                cell = g.cells[g.index(x, y)]
                cell.adjacent = sum(
                    1 for nx, ny in g.neighbors(x, y)
                    if g.cells[g.index(nx, ny)].mine
                )
        self.assertEqual(g.cells[g.index(1, 1)].adjacent, 8)

    def test_revealing_mine_loses(self):
        # Find a 3x3 single-mine board where (0,0) is NOT the mine, then
        # reveal the actual mine cell and expect a loss.
        mine_idx = None
        for seed in range(200):
            g = Game(width=3, height=3, mines=1, rng=random.Random(seed))
            g.reveal(0, 0)
            if not g.lost:
                mine_idx = next(i for i, c in enumerate(g.cells) if c.mine)
                break
        self.assertIsNotNone(mine_idx)
        x, y = mine_idx % 3, mine_idx // 3
        g.reveal(x, y)
        self.assertTrue(g.lost)


class VictoryTest(unittest.TestCase):
    def test_win_when_all_safe_revealed(self):
        g = Game(width=3, height=3, mines=1, rng=random.Random(7))
        # Reveal every non-mine forever until won/lost.
        for y in range(3):
            for x in range(3):
                g.reveal(x, y)
        if g.lost:
            # Retry with different mine layout (single mine, avoid corner).
            g = Game(width=3, height=3, mines=1, rng=random.Random(999))
            for y in range(3):
                for x in range(3):
                    if g.cells[g.index(x, y)].mine:
                        continue
                    g.reveal(x, y)
            self.assertTrue(g.won)
        else:
            self.assertTrue(g.won)


class ParseTest(unittest.TestCase):
    def test_plain_coords(self):
        self.assertEqual(parse_command("3 4"), ("reveal", 3, 4))

    def test_reveal_command(self):
        self.assertEqual(parse_command("r 2 5"), ("reveal", 2, 5))

    def test_flag_command(self):
        self.assertEqual(parse_command("f 0 1"), ("flag", 0, 1))

    def test_comma_separated(self):
        self.assertEqual(parse_command("r 3,4"), ("reveal", 3, 4))

    def test_malformed(self):
        self.assertIsNone(parse_command(""))
        self.assertIsNone(parse_command("r a b"))
        self.assertIsNone(parse_command("r 1"))


class BoardRenderTest(unittest.TestCase):
    def test_initial_render(self):
        g = Game(width=3, height=3, mines=1)
        text = Board(g).render()
        self.assertEqual(text.count("."), 9)

    def test_show_mines_reveals(self):
        g = Game(width=3, height=3, mines=1)
        g._place_mines()
        text = Board(g).render(show_mines=True)
        self.assertEqual(text.count("*"), 1)


if __name__ == "__main__":
    unittest.main()
