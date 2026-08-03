import math
import random
import unittest

from passgen import generate_passphrase, generate_password
from passgen.core import (
    PasswordConfig,
    entropy,
    generate_token,
    pool_size,
)


class RandomSource:
    """Deterministic stand-in for secrets.randbelow for testing."""

    def __init__(self, seed=0):
        self._rng = random.Random(seed)

    def __call__(self, upper_bound):
        return self._rng.randrange(upper_bound)


class GeneratePasswordTest(unittest.TestCase):
    def test_default_length(self):
        self.assertEqual(len(generate_password()), 16)

    def test_custom_length(self):
        self.assertEqual(len(generate_password(PasswordConfig(length=24))), 24)

    def test_all_pools_represented(self):
        rng = RandomSource(7)
        result = generate_password(
            PasswordConfig(
                length=64, lowercase=True, uppercase=True, digits=True,
                symbols=True, rng=rng,
            )
        )
        self.assertNotEqual(set(result) & set("abcdefghijklmnopqrstuvwxyz"), set())
        self.assertNotEqual(set(result) & set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), set())
        self.assertNotEqual(set(result) & set("0123456789"), set())
        self.assertNotEqual(set(result) & set("!@#$%^&*()-_=+[]{};:,.<>?"), set())

    def test_exclude_ambiguous(self):
        rng = RandomSource(3)
        result = generate_password(
            PasswordConfig(length=64, exclude_ambiguous=True, rng=rng)
        )
        self.assertNotIn("I", result)
        self.assertNotIn("l", result)
        self.assertNotIn("1", result)
        self.assertNotIn("O", result)
        self.assertNotIn("0", result)

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            generate_password(PasswordConfig(length=0))

    def test_deterministic_with_fresh_rng(self):
        a = generate_password(PasswordConfig(length=10, rng=RandomSource(42)))
        b = generate_password(PasswordConfig(length=10, rng=RandomSource(42)))
        self.assertEqual(a, b)


class GeneratePassphraseTest(unittest.TestCase):
    def test_word_count(self):
        result = generate_passphrase(words=5, wordlist=["alpha", "beta", "gamma"])
        self.assertEqual(len(result.split("-")), 5)
        for word in result.split("-"):
            self.assertIn(word, {"alpha", "beta", "gamma"})

    def test_separator(self):
        result = generate_passphrase(
            words=3, separator=".", rng=RandomSource(1),
            wordlist=["apple", "banana", "cherry"],
        )
        self.assertEqual(result.count("."), 2)
        self.assertNotIn("-", result)

    def test_capitalize(self):
        result = generate_passphrase(
            words=5, rng=RandomSource(2),
            wordlist=["apple", "banana", "cherry"], capitalize=True,
        )
        self.assertTrue(all(w[:1].isupper() for w in result.split("-")))

    def test_invalid_words(self):
        with self.assertRaises(ValueError):
            generate_passphrase(words=0)


class EntropyTest(unittest.TestCase):
    def test_known_value(self):
        self.assertAlmostEqual(entropy(94, 32), 32 * math.log2(94), places=6)

    def test_zero_length(self):
        self.assertEqual(entropy(94, 0), 0.0)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            entropy(0, 5)


class TokenTest(unittest.TestCase):
    def test_length(self):
        self.assertEqual(len(generate_token(length=20)), 20)

    def test_alphabet(self):
        rng = RandomSource(1)
        result = generate_token(length=10, alphabet="ab", rng=rng)
        self.assertLessEqual(set(result), set("ab"))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            generate_token(length=0)


class PoolSizeTest(unittest.TestCase):
    def test_default_pool(self):
        # 26 lowercase + 26 uppercase + 10 digits + 25 symbols = 87
        self.assertEqual(pool_size(PasswordConfig()), 87)


if __name__ == "__main__":
    unittest.main()
