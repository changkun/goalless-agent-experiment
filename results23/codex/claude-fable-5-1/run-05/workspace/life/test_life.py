import unittest

from life import PATTERNS, bounding_box, centered, parse_rle, render, step, translate


class ParseRleTests(unittest.TestCase):
    def test_glider(self):
        self.assertEqual(parse_rle("bo$2bo$3o!"), {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)})

    def test_multi_digit_runs_and_headers(self):
        text = "#C comment\nx = 12, y = 1\n12o!"
        self.assertEqual(parse_rle(text), {(x, 0) for x in range(12)})

    def test_multiple_row_skip(self):
        self.assertEqual(parse_rle("o3$o!"), {(0, 0), (0, 3)})

    def test_bad_token(self):
        with self.assertRaises(ValueError):
            parse_rle("oz!")


class StepTests(unittest.TestCase):
    def test_blinker_oscillates_with_period_two(self):
        blinker = parse_rle(PATTERNS["blinker"])
        self.assertNotEqual(step(blinker), blinker)
        self.assertEqual(step(step(blinker)), blinker)

    def test_glider_returns_translated_after_four_steps(self):
        glider = parse_rle(PATTERNS["glider"])
        cells = glider
        for _ in range(4):
            cells = step(cells)
        self.assertEqual(cells, translate(glider, 1, 1))

    def test_block_is_still_life(self):
        block = parse_rle("2o$2o!")
        self.assertEqual(step(block), block)

    def test_lonely_cell_dies(self):
        self.assertEqual(step(frozenset({(0, 0)})), frozenset())

    def test_pulsar_has_period_three(self):
        pulsar = parse_rle(PATTERNS["pulsar"])
        cells = pulsar
        for _ in range(3):
            cells = step(cells)
        self.assertEqual(cells, pulsar)

    def test_diehard_dies_at_generation_130(self):
        cells = parse_rle(PATTERNS["diehard"])
        for generation in range(1, 131):
            cells = step(cells)
            if not cells:
                self.assertEqual(generation, 130)
                break
        else:
            self.fail("diehard should be extinct by generation 130")

    def test_gosper_gun_emits_gliders(self):
        cells = parse_rle(PATTERNS["gosper-gun"])
        start = len(cells)
        for _ in range(120):
            cells = step(cells)
        self.assertGreater(len(cells), start)


class GeometryTests(unittest.TestCase):
    def test_bounding_box(self):
        self.assertEqual(bounding_box(frozenset({(2, 5), (-1, 7)})), (-1, 5, 2, 7))
        self.assertEqual(bounding_box(frozenset()), (0, 0, 0, 0))

    def test_centered(self):
        cells = centered(frozenset({(10, 10)}), 5, 5)
        self.assertEqual(cells, {(2, 2)})

    def test_render(self):
        art = render(frozenset({(0, 0), (1, 1)}), 2, 2, alive="#", dead=".")
        self.assertEqual(art, "#.\n.#")


if __name__ == "__main__":
    unittest.main()
