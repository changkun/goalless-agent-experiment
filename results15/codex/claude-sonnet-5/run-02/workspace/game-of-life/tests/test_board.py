import unittest

from gol.board import Board


class BoardTests(unittest.TestCase):
    def test_empty_board_stays_empty(self):
        board = Board()
        self.assertEqual(board.step(), Board())

    def test_block_still_life_is_stable(self):
        block = Board({(0, 0), (1, 0), (0, 1), (1, 1)})
        self.assertEqual(block.step(), block)

    def test_blinker_oscillates_with_period_two(self):
        horizontal = Board({(0, 0), (1, 0), (2, 0)})
        vertical = Board({(1, -1), (1, 0), (1, 1)})
        self.assertEqual(horizontal.step(), vertical)
        self.assertEqual(vertical.step(), horizontal)

    def test_glider_translates_after_four_generations(self):
        glider = Board.from_pattern(
            """
            .#.
            ..#
            ###
            """
        )
        advanced = glider
        for _ in range(4):
            advanced = advanced.step()

        shifted = Board({(x + 1, y + 1) for x, y in glider})
        self.assertEqual(advanced, shifted)

    def test_lone_cell_dies(self):
        lonely = Board({(5, 5)})
        self.assertEqual(lonely.step(), Board())

    def test_overpopulated_cell_dies(self):
        overcrowded = Board({(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)})
        self.assertNotIn((0, 0), overcrowded.step())

    def test_render_includes_padding_border(self):
        board = Board({(0, 0)})
        rendered = board.render(padding=1)
        lines = rendered.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line) == 3 for line in lines))
        self.assertEqual(lines[1][1], "#")

    def test_bounds_raises_on_empty_board(self):
        with self.assertRaises(ValueError):
            Board().bounds()


if __name__ == "__main__":
    unittest.main()
