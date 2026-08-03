import unittest

from golife.engine import Universe
from golife.patterns import get


class TestRules(unittest.TestCase):
    def test_block_stable(self):
        u = Universe(get("block").cells())
        before = frozenset(u.live)
        u.step()
        self.assertEqual(frozenset(u.live), before)

    def test_blinker_oscillates(self):
        u = Universe(get("blinker").cells())
        start = frozenset(u.live)
        for _ in range(2):
            u.step()
        self.assertEqual(frozenset(u.live), start)

    def test_glider_translates(self):
        u = Universe(get("glider").cells())
        shape0 = frozenset((x - 2, y - 1) for x, y in u.live)  # normalise near origin
        # A glider's shape repeats every 4 generations, translated by (1, 1).
        u.step(4)
        shape4 = frozenset((x - 3, y - 2) for x, y in u.live)
        self.assertEqual(shape0, shape4)

    def test_overpopulation_kills(self):
        # A full 3x3 block has a dead centre that stays dead but the ring
        # survives; exercising the 2/3 neighbour rules implicitly.
        u = Universe({(x, y) for x in range(3) for y in range(3)})
        u.step()
        self.assertEqual(u.generation, 1)
        self.assertTrue((1, 1) not in u.live)

    def test_empty_stays_empty(self):
        u = Universe()
        u.step()
        self.assertEqual(u.population, 0)

    def test_generation_counter(self):
        u = Universe(get("glider").cells())
        u.step(7)
        self.assertEqual(u.generation, 7)

    def test_toggle(self):
        u = Universe()
        u.toggle(0, 0)
        self.assertIn((0, 0), u.live)
        u.toggle(0, 0)
        self.assertNotIn((0, 0), u.live)

    def test_render_crop(self):
        u = Universe(get("block").cells())  # cells at (0,0),(1,0),(0,1),(1,1)
        self.assertEqual(u.render(), "##\n##")


class TestPatterns(unittest.TestCase):
    def test_all_patterns_parse(self):
        for name in ["block", "beehive", "blinker", "toad", "beacon",
                     "glider", "lwss", "r_pentomino", "pulsar"]:
            cells = get(name).cells()
            self.assertGreater(len(cells), 0, name)

    def test_alias_lookup(self):
        self.assertEqual(get("r_pentomino").name, "r_pentomino")


if __name__ == "__main__":
    unittest.main()
