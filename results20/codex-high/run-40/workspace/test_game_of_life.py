import importlib.util
import unittest

spec = importlib.util.spec_from_file_location("gol", "game_of_life.py")
gol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gol)


def bbox(cells):
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


class TestGameOfLife(unittest.TestCase):
    def test_blinker_oscillates(self):
        blinker = {(1, 0), (1, 1), (1, 2)}  # vertical
        assert gol.step(blinker) == {(0, 1), (1, 1), (2, 1)}  # horizontal

    def test_block_is_stable(self):
        block = {(0, 0), (1, 0), (0, 1), (1, 1)}
        self.assertEqual(gol.step(block), block)

    def test_glider_translates(self):
        g = set(gol.PRESETS["1"][1])
        for _ in range(4):
            g = gol.step(g)
        self.assertEqual(tuple(v + 1 for v in bbox(set(gol.PRESETS["1"][1]))), bbox(g))

    def test_pulsar_period_3(self):
        p = set(gol.PRESETS["3"][1])
        self.assertEqual(gol.step(gol.step(gol.step(p))), p)

    def test_gosper_gun_fires(self):
        state = set(gol.PRESETS["2"][1])
        for _ in range(200):
            state = gol.step(state)
        above = [c for c in state if c[1] < 15]
        self.assertGreater(len(above), 20)

    def test_empty_grid_stays_empty(self):
        self.assertEqual(gol.step(set()), set())

    def test_center_keeps_cells_in_bounds(self):
        w, h = 50, 20
        cells = gol.center(set(gol.PRESETS["2"][1]), w, h)
        self.assertTrue(all(0 <= x < w and 0 <= y < h for x, y in cells))


if __name__ == "__main__":
    unittest.main()
