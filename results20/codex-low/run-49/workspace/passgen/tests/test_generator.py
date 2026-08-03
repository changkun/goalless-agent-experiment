import unittest

from passgen.generator import generate, sample_indices


class SampleIndicesTest(unittest.TestCase):
    def test_unique_and_in_range(self):
        indices = sample_indices(10, 200)
        self.assertEqual(len(indices), 10)
        self.assertEqual(len(set(indices)), 10)
        self.assertTrue(all(0 <= i < 200 for i in indices))

    def test_count_equal_pool(self):
        indices = sample_indices(5, 5)
        self.assertEqual(sorted(indices), list(range(5)))

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            sample_indices(0, 5)

    def test_pool_too_small(self):
        with self.assertRaises(ValueError):
            sample_indices(6, 5)


class GenerateTest(unittest.TestCase):
    def test_default_no_duplicates(self):
        pp = generate(count=6)
        self.assertEqual(len(pp.words), 6)
        self.assertEqual(len(set(pp.words)), 6)

    def test_string_join(self):
        pp = generate(count=3, separator=" ")
        self.assertEqual(len(pp.as_str().split(" ")), 3)

    def test_entropy_positive(self):
        pp = generate(count=6)
        self.assertGreater(pp.entropy_bits, 0)

    def test_custom_separator(self):
        pp = generate(count=4, separator="_")
        parts = pp.as_str().split("_")
        self.assertEqual(len(parts), 4)

    def test_rejects_too_large_count(self):
        with self.assertRaises(ValueError):
            generate(count=10 ** 6)


if __name__ == "__main__":
    unittest.main()
