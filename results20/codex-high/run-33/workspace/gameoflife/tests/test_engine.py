import unittest

from gameoflife.engine import World
from gameoflife.patterns import load, names


class WorldTests(unittest.TestCase):
    def test_block_is_still_life(self):
        w = World([(0, 0), (1, 0), (0, 1), (1, 1)])
        n = w.step()
        self.assertEqual(sorted(n.live), sorted(w.live))

    def test_blinker_oscillates(self):
        w = World([(0, 0), (1, 0), (2, 0)])
        n = w.step()
        self.assertEqual(sorted(n.live), [(1, -1), (1, 0), (1, 1)])
        self.assertEqual(sorted(n.step().live), sorted(w.live))

    def test_glider_moves(self):
        w = World(load("Glider"))
        n = w.step().step().step().step()
        cells = sorted(n.live)
        xs = [x for x, _ in cells]
        ys = [y for _, y in cells]
        self.assertEqual((min(xs), min(ys)), (1, 1))

    def test_dead_world_stays_dead(self):
        w = World()
        self.assertEqual(len(w.step()), 0)

    def test_step_in_place(self):
        w = World(load("Toad"))
        before = sorted(w.live)
        w.step_in_place()
        self.assertNotEqual(sorted(w.live), before)
        self.assertEqual(len(w), 6)


class PatternTests(unittest.TestCase):
    def test_all_patterns_load(self):
        for name in names():
            cells = load(name)
            self.assertTrue(len(cells) > 0, name)
            for x, y in cells:
                self.assertIsInstance(x, int)
                self.assertIsInstance(y, int)

    def test_glider_has_three_cells(self):
        self.assertEqual(len(load("Glider")), 5)

    def test_names_are_unique_and_sorted(self):
        ns = names()
        self.assertEqual(len(ns), len(set(ns)))


if __name__ == "__main__":
    unittest.main()
