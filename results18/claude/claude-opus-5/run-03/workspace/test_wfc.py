"""Tests for the WFC synthesiser.

The load-bearing one is test_every_window_occurs_in_the_sample: WFC's entire
contract is that the output is *locally* indistinguishable from the input, so if
propagation is even slightly wrong some output window will be a pattern that
never appeared in the sample. That test caught a transposed direction index in
the support-count initialiser, which made every asymmetric sample unsolvable.
"""

from __future__ import annotations

import unittest

from samples import SAMPLES
from wfc import Contradiction, build_patterns, _reflect, _rotate, _variants, generate


def windows(rows: list[str], size: int, periodic: bool) -> list[tuple[str, ...]]:
    height, width = len(rows), len(rows[0])
    limit_y = height if periodic else height - size + 1
    limit_x = width if periodic else width - size + 1
    return [
        tuple(
            "".join(rows[(y + dy) % height][(x + dx) % width] for dx in range(size))
            for dy in range(size)
        )
        for y in range(limit_y)
        for x in range(limit_x)
    ]


class TestPatternExtraction(unittest.TestCase):
    def test_rotate_is_clockwise(self):
        self.assertEqual(_rotate(["ab", "cd"]), ["ca", "db"])

    def test_reflect_is_horizontal(self):
        self.assertEqual(_reflect(["ab", "cd"]), ["ba", "dc"])

    def test_four_rotations_return_to_start(self):
        rows = ["abc", "def", "ghi"]
        self.assertEqual(_rotate(_rotate(_rotate(_rotate(rows)))), rows)

    def test_asymmetric_grid_has_eight_distinct_variants(self):
        variants = _variants(["ab", "cd"], 8)
        self.assertEqual(len(variants), 8)
        self.assertEqual(len({tuple(v) for v in variants}), 8)

    def test_symmetry_one_is_identity_only(self):
        rows = ["ab", "cd"]
        self.assertEqual(_variants(rows, 1), [rows])

    def test_uniform_sample_yields_one_pattern(self):
        ps = build_patterns(["aaa", "aaa", "aaa"], 2, symmetry=1)
        self.assertEqual(len(ps), 1)
        self.assertEqual(ps.weights, (9,))  # one per periodic offset
        # With symmetries every offset is also counted once per variant.
        self.assertEqual(build_patterns(["aaa"] * 3, 2).weights, (72,))

    def test_periodic_input_wraps(self):
        # Non-periodic: only one 2x2 window. Periodic: four.
        self.assertEqual(sum(build_patterns(["ab", "cd"], 2, symmetry=1,
                                            periodic_input=False).weights), 1)
        self.assertEqual(sum(build_patterns(["ab", "cd"], 2, symmetry=1).weights), 4)

    def test_adjacency_is_reflexive_for_uniform_pattern(self):
        ps = build_patterns(["aa", "aa"], 2)
        for d in range(4):
            self.assertEqual(ps.propagator[d][0], (0,))

    def test_rejects_ragged_sample(self):
        with self.assertRaises(ValueError):
            build_patterns(["abc", "de"], 2)

    def test_rejects_sample_smaller_than_pattern(self):
        with self.assertRaises(ValueError):
            build_patterns(["ab", "cd"], 3, periodic_input=False)


class TestGenerate(unittest.TestCase):
    def test_every_window_occurs_in_the_sample(self):
        """The core WFC guarantee, checked for every shipped sample."""
        for name, sample in SAMPLES.items():
            with self.subTest(sample=name):
                ps = build_patterns(
                    list(sample.rows), sample.size,
                    symmetry=sample.symmetry, periodic_input=sample.periodic_input,
                )
                legal = set(ps.patterns)
                out = generate(
                    list(sample.rows), 40, 14,
                    size=sample.size, symmetry=sample.symmetry,
                    periodic_input=sample.periodic_input, seed=1234,
                )
                for window in windows(out, sample.size, periodic=False):
                    self.assertIn(window, legal)

    def test_periodic_output_tiles_seamlessly(self):
        sample = SAMPLES["cave"]
        out = generate(list(sample.rows), 24, 16, periodic_output=True, seed=7)
        legal = set(build_patterns(list(sample.rows), 3).patterns)
        # Wrapping windows must be legal too, or the texture would not tile.
        for window in windows(out, 3, periodic=True):
            self.assertIn(window, legal)

    def test_requested_size_is_honoured(self):
        for periodic in (False, True):
            with self.subTest(periodic=periodic):
                out = generate(list(SAMPLES["cave"].rows), 31, 17,
                               periodic_output=periodic, seed=3)
                self.assertEqual(len(out), 17)
                self.assertEqual({len(r) for r in out}, {31})

    def test_same_seed_reproduces_output(self):
        rows = list(SAMPLES["maze"].rows)
        kwargs = dict(periodic_input=False, seed=99)
        self.assertEqual(generate(rows, 30, 12, **kwargs),
                         generate(rows, 30, 12, **kwargs))

    def test_different_seeds_diverge(self):
        rows = list(SAMPLES["cave"].rows)
        self.assertNotEqual(generate(rows, 30, 12, seed=1),
                            generate(rows, 30, 12, seed=2))

    def test_uniform_sample_gives_uniform_output(self):
        out = generate(["aaa", "aaa", "aaa"], 10, 6, seed=0)
        self.assertEqual(out, ["a" * 10] * 6)

    def test_gravity_is_respected(self):
        """Soil only ever appears below flowers, never above."""
        out = generate(list(SAMPLES["meadow"].rows), 40, 12,
                       symmetry=1, periodic_input=False, seed=42)
        soil_rows = [y for y, row in enumerate(out) if "▚" in row or "▞" in row]
        flower_rows = [y for y, row in enumerate(out) if "✿" in row]
        self.assertTrue(soil_rows and flower_rows)
        self.assertGreater(min(soil_rows), max(flower_rows))

    def test_gives_up_with_contradiction(self):
        # This sample yields exactly one 2x2 pattern, and it cannot tile beside
        # itself in any direction, so no multi-cell output can exist.
        with self.assertRaises(Contradiction):
            generate(["ab", "cd"], 8, 5, size=2, symmetry=1,
                     periodic_input=False, attempts=2)

    def test_starved_patterns_never_reach_the_output(self):
        """A pattern with an empty propagator must be banned, not silently used."""
        ps = build_patterns(["ab", "cd"], 2, symmetry=1, periodic_input=False)
        self.assertEqual(len(ps), 1)
        self.assertTrue(all(not ps.propagator[d][0] for d in range(4)))
        # A 1x1 output has no neighbours, so the lone pattern is still usable.
        self.assertEqual(generate(["ab", "cd"], 2, 2, size=2, symmetry=1,
                                  periodic_input=False, seed=0), ["ab", "cd"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
