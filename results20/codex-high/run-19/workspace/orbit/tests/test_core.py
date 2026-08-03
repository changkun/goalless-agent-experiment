import unittest

from orbit.core import PLANETS, get_planet, scale_diameter


class PlanetTests(unittest.TestCase):
    def test_has_eight_planets(self) -> None:
        self.assertEqual(len(PLANETS), 8)

    def test_names_unique(self) -> None:
        names = [p.name for p in PLANETS]
        self.assertEqual(len(names), len(set(names)))

    def test_ordered_from_sun(self) -> None:
        self.assertEqual([p.name for p in PLANETS], [
            "Mercury", "Venus", "Earth", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune",
        ])

    def test_get_planet_case_insensitive(self) -> None:
        self.assertEqual(get_planet("mars").name, "Mars")
        self.assertEqual(get_planet("MARS").name, "Mars")

    def test_get_planet_unknown_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_planet("pluto")


class ScaleTests(unittest.TestCase):
    def test_largest_planet_is_full_width(self) -> None:
        self.assertEqual(scale_diameter(142984), "#" * 24)

    def test_smallest_planet_is_at_least_one_char(self) -> None:
        self.assertGreaterEqual(len(scale_diameter(4879)), 1)

    def test_scaling_is_monotonic(self) -> None:
        sizes = sorted(p.diameter_km for p in PLANETS)
        widths = [len(scale_diameter(s)) for s in sizes]
        self.assertEqual(widths, sorted(widths))


if __name__ == "__main__":
    unittest.main()
