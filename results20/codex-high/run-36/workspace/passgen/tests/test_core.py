"""Tests for passgen.core (uses stdlib unittest, no external deps)."""

import unittest

from passgen import StrengthError, analyze_strength, generate_password
from passgen.core import AMBIGUOUS, DIGITS, LOWER, SYMBOLS, UPPER


class GenerateTests(unittest.TestCase):
    def test_default_length_and_charset(self):
        pw = generate_password()
        self.assertEqual(len(pw), 16)
        self.assertTrue(any(c in LOWER for c in pw))
        self.assertTrue(any(c in UPPER for c in pw))
        self.assertTrue(any(c in DIGITS for c in pw))
        self.assertTrue(any(c in SYMBOLS for c in pw))

    def test_respects_disabled_groups(self):
        pw = generate_password(lowercase=False, digits=False)
        self.assertFalse(any(c in LOWER for c in pw))
        self.assertFalse(any(c in DIGITS for c in pw))
        self.assertTrue(any(c in UPPER for c in pw))
        self.assertTrue(any(c in SYMBOLS for c in pw))

    def test_excludes_ambiguous(self):
        pw = generate_password(200, exclude_ambiguous=True)
        self.assertFalse(any(c in AMBIGUOUS for c in pw))

    def test_respects_length(self):
        self.assertEqual(len(generate_password(length=24)), 24)
        self.assertEqual(len(generate_password(length=8)), 8)

    def test_requires_at_least_one_group(self):
        with self.assertRaises(StrengthError):
            generate_password(
                lowercase=False, uppercase=False, digits=False, symbols=False
            )

    def test_requires_length_for_groups(self):
        with self.assertRaises(StrengthError):
            generate_password(
                length=3, lowercase=True, uppercase=True, digits=True, symbols=True
            )

    def test_output_is_random(self):
        self.assertNotEqual(generate_password(), generate_password())

    def test_guarantees_each_group_represented(self):
        for _ in range(20):
            pw = generate_password(8)
            self.assertTrue(any(c in LOWER for c in pw))
            self.assertTrue(any(c in UPPER for c in pw))
            self.assertTrue(any(c in DIGITS for c in pw))
            self.assertTrue(any(c in SYMBOLS for c in pw))


class AnalyzeTests(unittest.TestCase):
    def test_weak_password(self):
        info = analyze_strength("abc")
        self.assertEqual(info["grade"], "very weak")
        self.assertEqual(info["length"], 3)
        self.assertEqual(info["score"], 1)

    def test_strong_password(self):
        info = analyze_strength("CorrectHorseBatteryStaple!9")
        self.assertIn(info["grade"], {"strong", "very strong"})
        self.assertEqual(info["score"], 4)
        self.assertGreater(info["entropy_bits"], 100)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            analyze_strength("")

    def test_reports_charset(self):
        info = analyze_strength("Ab1!")
        self.assertEqual(
            info["charset_used"],
            {
                "lowercase": True,
                "uppercase": True,
                "digits": True,
                "symbols": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
