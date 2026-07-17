import unittest

from gol import patterns
from gol.grid import Grid
from gol.png import write_png
from gol.sim import Simulation, parse_rule, soup_grid, sparkline

import random
import os
import tempfile


class TestGrid(unittest.TestCase):
    def test_wraparound(self):
        g = Grid(4, 4)
        g.set(-1, -1, 1)
        self.assertEqual(g.get(3, 3), 1)

    def test_population(self):
        g = Grid(5, 5)
        for i in range(3):
            g.set(i, 0, 1)
        self.assertEqual(g.population(), 3)

    def test_bad_dimensions(self):
        with self.assertRaises(ValueError):
            Grid(0, 5)


class TestRules(unittest.TestCase):
    def test_parse_conway(self):
        birth, survive = parse_rule("B3/S23")
        self.assertEqual(birth, {3})
        self.assertEqual(survive, {2, 3})

    def test_parse_highlife(self):
        birth, survive = parse_rule("B36/S23")
        self.assertEqual(birth, {3, 6})

    def test_parse_garbage(self):
        with self.assertRaises(ValueError):
            parse_rule("nonsense")


class TestEvolution(unittest.TestCase):
    def test_block_is_still(self):
        g = Grid(8, 8)
        patterns.stamp(g, "block", 3, 3)
        sim = Simulation(g)
        before = g.ascii()
        sim.step()
        self.assertEqual(g.ascii(), before)

    def test_blinker_oscillates(self):
        g = Grid(7, 7)
        patterns.stamp(g, "blinker", 2, 3)
        sim = Simulation(g)
        horizontal = g.ascii()
        sim.step()
        vertical = g.ascii()
        self.assertNotEqual(horizontal, vertical)
        sim.step()
        self.assertEqual(g.ascii(), horizontal)

    def test_glider_translates(self):
        g = Grid(16, 16)
        patterns.stamp(g, "glider", 2, 2)
        sim = Simulation(g)
        sim.step()
        sim.step()
        sim.step()
        sim.step()
        self.assertEqual(g.population(), 5)
        cells = [
            (x, y) for y in range(16) for x in range(16) if g.get(x, y)
        ]
        min_x = min(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        self.assertEqual((min_x, min_y), (3, 3))

    def test_diehard_vanishes_at_130(self):
        g = Grid(40, 40)
        patterns.stamp(g, "diehard", 10, 10)
        sim = Simulation(g)
        outcome, tick = sim.run_until_settled(max_ticks=500)
        self.assertEqual(outcome, "extinct")
        self.assertEqual(tick, 130)

    def test_cycle_detection(self):
        g = Grid(16, 16)
        patterns.stamp(g, "pulsar", 1, 1)
        sim = Simulation(g)
        outcome, detail = sim.run_until_settled(max_ticks=100)
        self.assertEqual(outcome, "cycle")
        period, _ = detail
        self.assertEqual(period, 3)


class TestSoupAndSeries(unittest.TestCase):
    def test_soup_density_roughly(self):
        rng = random.Random(1)
        g = soup_grid(50, 50, 0.25, rng)
        pop = g.population()
        self.assertTrue(400 < pop < 850, f"density way off: {pop}")

    def test_sparkline_shape(self):
        line = sparkline([1, 5, 3, 9, 2], width=5)
        self.assertEqual(len(line), 5)


class TestPng(unittest.TestCase):
    def test_writes_valid_header(self):
        rows = [bytearray(b"\xff\x00\x00" * 4) for _ in range(4)]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.png")
            write_png(path, 4, 4, rows)
            with open(path, "rb") as fh:
                magic = fh.read(8)
        self.assertEqual(magic, b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
