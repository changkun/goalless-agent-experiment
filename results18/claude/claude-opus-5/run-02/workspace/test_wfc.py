#!/usr/bin/env python3
"""Checks on wfc.py, the important one being local validity.

Wave Function Collapse promises that every NxN patch of the output already
occurs in the sample. That is the whole contract, and it is cheap to verify
directly: harvest the output and check it introduces no new patch.
"""

import random
import sys
import unittest

import wfc


def generate(name, w, h, n, seed, periodic=False):
    spec = wfc.SAMPLES[name]
    patterns, weights, from_top, from_bottom = wfc.harvest(
        spec["art"], n, spec["symmetry"], spec["periodic"]
    )
    compat = wfc.compatibility(patterns, n)
    wave = wfc.Wave(weights, compat, w, h, periodic, random.Random(seed))
    observed = wave.solve()
    assert observed is not None, f"{name}: no solution at seed {seed}"
    rows = wfc.to_chars(observed, patterns, n, w, h, periodic)
    return rows, set(patterns)


def patches(rows, n, periodic):
    """Every NxN patch of a rendered grid, as pattern tuples."""
    h, w = len(rows), len(rows[0])
    ys = range(h) if periodic else range(h - n + 1)
    xs = range(w) if periodic else range(w - n + 1)
    for oy in ys:
        for ox in xs:
            yield ox, oy, tuple(
                rows[(oy + dy) % h][(ox + dx) % w]
                for dy in range(n)
                for dx in range(n)
            )


class TestHarvest(unittest.TestCase):
    def test_rotate_four_times_is_identity(self):
        p = tuple("abcdefghi")
        q = p
        for _ in range(4):
            q = wfc._rotate(q, 3)
        self.assertEqual(p, q)

    def test_reflect_twice_is_identity(self):
        p = tuple("abcdefghi")
        self.assertEqual(p, wfc._reflect(wfc._reflect(p, 3), 3))

    def test_variant_count_is_capped_by_symmetry(self):
        p = tuple("abcdefghi")  # fully asymmetric, so no variants collapse
        for sym in (1, 2, 4, 8):
            self.assertEqual(len(set(wfc._variants(p, 3, sym))), sym)

    def test_uniform_sample_yields_one_pattern(self):
        art = "\n".join(["...."] * 4)
        patterns, weights, _, _ = wfc.harvest(art, 2, 1, True)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(weights, [16])  # 4x4 anchors, wrapping

    def test_agrees_is_symmetric(self):
        patterns, _, _, _ = wfc.harvest(wfc.SAMPLES["cave"]["art"], 3, 1, True)
        for a in patterns[:12]:
            for b in patterns[:12]:
                # b sits to the right of a iff a sits to the left of b.
                self.assertEqual(
                    wfc._agrees(a, b, 1, 0, 3), wfc._agrees(b, a, -1, 0, 3)
                )

    def test_edge_rows_recorded(self):
        # Non-periodic harvest of a sample whose first and last rows are unique.
        art = "aaaa\nbbbb\ncccc\ndddd"
        patterns, _, top, bottom = wfc.harvest(art, 2, 1, False)
        self.assertTrue(all(patterns[i][0] == "a" for i in top))
        self.assertTrue(all(patterns[i][0] == "c" for i in bottom))


class TestLocalValidity(unittest.TestCase):
    """The contract: output patches must all come from the sample."""

    def check(self, name, n=3, w=40, h=20, periodic=False, seeds=(1, 2, 3)):
        for seed in seeds:
            rows, allowed = generate(name, w, h, n, seed, periodic)
            self.assertEqual([len(r) for r in rows], [w] * h)
            self.assertEqual(len(rows), h)
            for ox, oy, patch in patches(rows, n, periodic):
                self.assertIn(
                    patch,
                    allowed,
                    f"{name} seed={seed}: patch at ({ox},{oy}) "
                    f"{''.join(patch)!r} never occurs in the sample",
                )

    def test_islands(self):
        self.check("islands")

    def test_cave(self):
        self.check("cave")

    def test_rooms(self):
        self.check("rooms")

    def test_circuit(self):
        self.check("circuit")

    def test_flowers(self):
        self.check("flowers")

    def test_patch_size_two(self):
        self.check("cave", n=2)

    def test_patch_size_four(self):
        self.check("islands", n=4, w=30, h=16, seeds=(1,))

    def test_periodic_output_wraps_seamlessly(self):
        # With periodic=True the wrap-around patches are checked too, so a
        # seam would show up as a patch the sample never contained.
        self.check("cave", periodic=True, w=24, h=16)
        self.check("islands", periodic=True, w=24, h=16)

    def test_narrow_and_short_grids(self):
        # w or h == n is the tight case: the edge renderer must not step off
        # the grid and wrap around to the far side.
        self.check("cave", w=4, h=4, seeds=(1,))
        self.check("cave", w=64, h=3, seeds=(1,))
        self.check("cave", w=3, h=40, seeds=(1,))
        self.check("cave", w=3, h=3, seeds=(1,))


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_output(self):
        a, _ = generate("islands", 30, 12, 3, 99)
        b, _ = generate("islands", 30, 12, 3, 99)
        self.assertEqual(a, b)

    def test_different_seed_different_output(self):
        a, _ = generate("islands", 40, 20, 3, 1)
        b, _ = generate("islands", 40, 20, 3, 2)
        self.assertNotEqual(a, b)


class TestSolver(unittest.TestCase):
    def test_contradiction_is_reported_not_raised(self):
        # An impossible seed mask must come back as None, not an exception.
        patterns, weights, _, _ = wfc.harvest(
            wfc.SAMPLES["cave"]["art"], 3, 8, True
        )
        compat = wfc.compatibility(patterns, 3)
        wave = wfc.Wave(weights, compat, 10, 10, False, random.Random(0))
        self.assertIsNone(wave.solve(seeds=[(0, 0)]))

    def test_seed_mask_is_honoured(self):
        spec = wfc.SAMPLES["cave"]
        patterns, weights, _, _ = wfc.harvest(spec["art"], 3, 8, True)
        compat = wfc.compatibility(patterns, 3)
        solid = next(i for i, p in enumerate(patterns) if set(p) == {"#"})
        wave = wfc.Wave(weights, compat, 20, 12, False, random.Random(4))
        observed = wave.solve(seeds=[(0, 1 << solid)])
        self.assertIsNotNone(observed)
        self.assertEqual(observed[0], solid)

    def test_entropy_falls_as_options_are_removed(self):
        w = wfc.Wave([1, 1, 1, 1], [[0] * 4] * 4, 4, 4, False, random.Random(0))
        self.assertGreater(w.entropy(0b1111), w.entropy(0b11))
        self.assertAlmostEqual(w.entropy(0b1), 0.0)

    def test_union_matches_a_plain_loop(self):
        spec = wfc.SAMPLES["rooms"]
        patterns, weights, _, _ = wfc.harvest(spec["art"], 3, 8, True)
        compat = wfc.compatibility(patterns, 3)
        w = wfc.Wave(weights, compat, 8, 8, False, random.Random(0))
        rng = random.Random(11)
        for _ in range(40):
            mask = rng.randrange(1, 1 << len(patterns))
            for d in range(4):
                want = 0
                for p in range(len(patterns)):
                    if mask >> p & 1:
                        want |= compat[d][p]
                self.assertEqual(w.union(mask, d), want)


class TestCLI(unittest.TestCase):
    def test_list(self):
        self.assertEqual(wfc.main(["--list"]), 0)

    def test_unknown_sample(self):
        self.assertEqual(wfc.main(["nope"]), 2)

    def test_bad_patch_size(self):
        self.assertEqual(wfc.main(["cave", "-n", "1"]), 2)

    def test_generate_every_sample(self):
        for name in wfc.SAMPLES:
            self.assertEqual(
                wfc.main([name, "-W", "40", "-H", "12", "-s", "5", "--plain"]),
                0,
                f"{name} failed to generate",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
