import math
import unittest

import passgen


class TestPassword(unittest.TestCase):
    def test_default_length(self):
        pw = passgen.generate_password()
        self.assertEqual(len(pw), 16)

    def test_length_respected(self):
        for n in (4, 12, 32):
            pw = passgen.generate_password(n)
            self.assertEqual(len(pw), n)

    def test_all_classes_guaranteed(self):
        # Every enabled class must appear at least once.
        pw = passgen.generate_password(20, lower=True, upper=True,
                                       digits=True, symbols=True)
        self.assertTrue(any(c.islower() for c in pw))
        self.assertTrue(any(c.isupper() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))
        self.assertTrue(any(c in passgen.SYMBOLS for c in pw))

    def test_exclusion(self):
        pw = passgen.generate_password(20, upper=False, digits=False,
                                       symbols=False)
        self.assertTrue(all(c.islower() for c in pw))

    def test_no_classes_raises(self):
        with self.assertRaises(ValueError):
            passgen.generate_password(16, lower=False, upper=False,
                                      digits=False, symbols=False)

    def test_length_too_short_raises(self):
        # 3 char classes enabled but length 2 -> too short.
        with self.assertRaises(ValueError):
            passgen.generate_password(2, lower=True, upper=True, digits=True,
                                      symbols=False)

    def test_stochastic_variety(self):
        # Trivially should never produce all-same output across many draws.
        outputs = {passgen.generate_password(16) for _ in range(200)}
        self.assertGreater(len(outputs), 150)


class TestPassphrase(unittest.TestCase):
    def test_word_count(self):
        for n in (3, 6, 10):
            ph = passgen.generate_passphrase(n)
            self.assertEqual(len(ph.split()), n)

    def test_words_from_vocab(self):
        vocab = set(passgen._DEFAULT_WORDS)
        ph = passgen.generate_passphrase(8)
        for w in ph.split():
            self.assertIn(w, vocab)

    def test_custom_separator(self):
        ph = passgen.generate_passphrase(4, separator="-")
        self.assertEqual(len(ph.split("-")), 4)
        self.assertNotIn(" ", ph)

    def test_zero_words_raises(self):
        with self.assertRaises(ValueError):
            passgen.generate_passphrase(0)


class TestEntropy(unittest.TestCase):
    def test_entropy_formula(self):
        # Full defaults: lowercase+upper+digits = 26+26+10 = 62 chars, len 16
        bits = passgen.password_entropy("x" * 16, lower=True, upper=True,
                                        digits=True, symbols=False)
        self.assertAlmostEqual(bits, 16 * math.log2(62), places=6)

    def test_passphrase_entropy(self):
        bits = passgen.passphrase_entropy(6)
        self.assertAlmostEqual(bits, 6 * math.log2(len(passgen._DEFAULT_WORDS)),
                               places=6)

    def test_entropy_length_required(self):
        # pool 62, want >= 100 bits -> ceil(100 / log2(62)) = 17
        n = passgen.entropy_length_required(62, 100)
        self.assertEqual(n, 17)
        # And it should actually meet the target:
        self.assertGreaterEqual(n * math.log2(62), 100)

    def test_cli_entropy_mode_password(self):
        rc = passgen.main(["password", "--entropy", "100"])
        self.assertEqual(rc, 0)

    def test_cli_entropy_mode_passphrase(self):
        rc = passgen.main(["passphrase", "--entropy", "100"])
        self.assertEqual(rc, 0)


class TestCLI(unittest.TestCase):
    def test_password_command(self):
        self.assertEqual(passgen.main(["password"]), 0)

    def test_passphrase_command(self):
        self.assertEqual(passgen.main(["passphrase"]), 0)

    def test_invalid_mode(self):
        with self.assertRaises(SystemExit):
            passgen.main(["bogus"])


if __name__ == "__main__":
    unittest.main()
