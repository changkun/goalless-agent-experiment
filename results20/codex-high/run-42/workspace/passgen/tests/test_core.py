import math
import random
import unittest

from passgen.core import (
    DEFAULT_WORDLIST,
    entropy,
    generate_password,
    generate_passphrase,
)
from passgen import main


class DeterministicRng:
    """Minimal RNG stub so tests are reproducible."""

    def __init__(self, values):
        self.values = list(values)
        self.pool = None

    def choice(self, pool):
        self.pool = pool
        if self.values:
            return self.values.pop(0)
        return pool[0]


class EntropyTests(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(entropy(2, 1), 1.0)
        self.assertAlmostEqual(entropy(2, 10), 10.0)

    def test_zero_pool(self):
        self.assertEqual(entropy(0, 5), 0.0)

    def test_negative_length(self):
        self.assertEqual(entropy(4, -1), 0.0)

    def test_matches_math(self):
        self.assertAlmostEqual(entropy(len(DEFAULT_WORDLIST), 5),
                              5 * math.log2(len(DEFAULT_WORDLIST)))


class PasswordTests(unittest.TestCase):
    def test_length_and_classes(self):
        classes = "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
            "0123456789" "!@#$%^&*()-_=+[]{};:,.<>?"
        seen_lower = seen_upper = seen_digit = seen_symbol = False
        for _ in range(200):
            p = generate_password(12)
            self.assertEqual(len(p), 12)
            for c in p:
                self.assertIn(c, classes)
            seen_lower = seen_lower or any(c.islower() for c in p)
            seen_upper = seen_upper or any(c.isupper() for c in p)
            seen_digit = seen_digit or any(c.isdigit() for c in p)
            seen_symbol = seen_symbol or any(
                c in "!@#$%^&*()-_=+[]{};:,.<>?" for c in p)
        # Across many samples every enabled class should appear at least once.
        self.assertTrue(seen_lower)
        self.assertTrue(seen_upper)
        self.assertTrue(seen_digit)
        self.assertTrue(seen_symbol)

    def test_excluded_class_not_used(self):
        p = generate_password(30, digits=False, symbols=False)
        self.assertTrue(p.isalpha())

    def test_password_is_not_all_same(self):
        sample = {generate_password(64) for _ in range(50)}
        self.assertGreater(len(sample), 1)

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            generate_password(0)

    def test_no_classes(self):
        with self.assertRaises(ValueError):
            generate_password(10, lowercase=False, uppercase=False,
                              digits=False, symbols=False)

    def test_deterministic_rng(self):
        rng = DeterministicRng(["a", "b", "c", "d"])
        p = generate_password(4, rng=rng)
        self.assertEqual(p, "abcd")


class PassphraseTests(unittest.TestCase):
    def test_word_count(self):
        p = generate_passphrase(6)
        self.assertEqual(len(p.split("-")), 6)

    def test_all_words_from_wordlist(self):
        for _ in range(20):
            p = generate_passphrase(8)
            for word in p.split("-"):
                self.assertIn(word, DEFAULT_WORDLIST)

    def test_custom_separator(self):
        p = generate_passphrase(3, separator=".")
        self.assertEqual(len(p.split(".")), 3)

    def test_capitalize(self):
        p = generate_passphrase(4, capitalize=True)
        for word in p.split("-"):
            self.assertEqual(word[:1], word[:1].upper())

    def test_number_suffix(self):
        p = generate_passphrase(3, number=True)
        suffix = p.rsplit("-", 1)[1]
        self.assertEqual(len(suffix), 2)
        self.assertTrue(suffix.isdigit())

    def test_invalid_words(self):
        with self.assertRaises(ValueError):
            generate_passphrase(0)

    def test_empty_wordlist(self):
        with self.assertRaises(ValueError):
            generate_passphrase(3, wordlist=[])

    def test_deterministic_rng(self):
        rng = DeterministicRng(["amber", "bass", "coral"])
        p = generate_passphrase(3, rng=rng)
        self.assertEqual(p, "amber-bass-coral")


class CliTests(unittest.TestCase):
    def test_version(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_default_is_passphrase_verbose(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["-n", "2", "-w", "4", "-v"])
        self.assertEqual(rc, 0)
        lines = buf.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn("bits", line)

    def test_verbose_password_has_entropy(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--password", "-l", "16", "-v"])
        self.assertEqual(rc, 0)
        self.assertIn("bits", buf.getvalue())

    def test_no_classes_is_error(self):
        with self.assertRaises(SystemExit):
            main(["--password", "--no-lower", "--no-upper",
                  "--no-digits", "--no-symbols"])

    def test_zero_count_is_error(self):
        with self.assertRaises(SystemExit):
            main(["-n", "0"])


if __name__ == "__main__":
    unittest.main()
