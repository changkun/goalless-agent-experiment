import unittest

from life.life import PATTERNS, parse, render, step


class StepTests(unittest.TestCase):
    def test_empty_stays_empty(self):
        self.assertEqual(step(frozenset()), frozenset())

    def test_lonely_cell_dies(self):
        self.assertEqual(step(frozenset({(0, 0)})), frozenset())

    def test_block_is_still_life(self):
        block = parse("##\n##")
        self.assertEqual(step(block), block)

    def test_blinker_oscillates_with_period_two(self):
        horizontal = parse(PATTERNS["blinker"])
        vertical = step(horizontal)
        self.assertEqual(vertical, frozenset({(1, -1), (1, 0), (1, 1)}))
        self.assertEqual(step(vertical), horizontal)

    def test_glider_translates_by_one_diagonal_every_four_generations(self):
        glider = parse(PATTERNS["glider"])
        board = glider
        for _ in range(4):
            board = step(board)
        shifted = frozenset((x + 1, y + 1) for x, y in glider)
        self.assertEqual(board, shifted)

    def test_gosper_gun_emits_a_glider(self):
        board = parse(PATTERNS["gosper-gun"])
        before = len(board)
        for _ in range(30):
            board = step(board)
        self.assertEqual(len(board), before + 5)


class RenderTests(unittest.TestCase):
    def test_render_marks_live_cells(self):
        out = render(parse("#.\n.#"), width=2, height=2)
        self.assertEqual(out, "█·\n·█")


if __name__ == "__main__":
    unittest.main()
