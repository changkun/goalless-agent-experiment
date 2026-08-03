import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from starfield.generator import DEFAULT_PALETTE, generate


class TestGenerator(unittest.TestCase):
    def test_dimensions(self):
        rows = generate(6, 4, seed=1)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(len(row) == 6 for row in rows))

    def test_deterministic_with_seed(self):
        a = generate(40, 10, seed=42)
        b = generate(40, 10, seed=42)
        c = generate(40, 10, seed=43)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_only_palette_chars(self):
        rows = generate(100, 20, seed=7)
        allowed = set(DEFAULT_PALETTE)
        self.assertTrue(set("".join(rows)) <= allowed)

    def test_density_zero_has_no_stars(self):
        rows = generate(50, 10, density=0.0)
        self.assertTrue(all(set(row) <= {"."} for row in rows))

    def test_density_one_all_stars(self):
        rows = generate(50, 10, density=1.0, palette=(" ", "*"))
        self.assertTrue(all(set(row) <= {"*"} for row in rows))

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            generate(0, 5)
        with self.assertRaises(ValueError):
            generate(5, -1)

    def test_invalid_density(self):
        with self.assertRaises(ValueError):
            generate(5, 5, density=-0.1)
        with self.assertRaises(ValueError):
            generate(5, 5, density=1.5)

    def test_invalid_palette(self):
        with self.assertRaises(ValueError):
            generate(5, 5, palette=(" ",))


if __name__ == "__main__":
    unittest.main()
