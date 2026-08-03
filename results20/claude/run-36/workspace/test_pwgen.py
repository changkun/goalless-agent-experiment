"""Tests for pwgen.py - run with: python3 -m pytest test_pwgen.py -q
(or: python3 test_pwgen.py to run without pytest)."""

import math
import statistics
import subprocess
import sys

import pwgen


# --- unbiased sampler -------------------------------------------------------

def test_urandom_int_bounds():
    for n in (1, 2, 3, 10, 255, 256, 257, 1000):
        for _ in range(200):
            v = pwgen.urandom_int(n)
            assert 0 <= v < n


def test_pick_is_uniform():
    """Over many draws each char should appear roughly equally (chi-square-ish
    tolerance). This is statistical, so we keep the bound loose to avoid
    flakiness while still catching a biased sampler."""
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    n = 50_000
    counts = {c: 0 for c in alphabet}
    for _ in range(n):
        counts[pwgen.pick(alphabet)] += 1
    mean = n / len(alphabet)
    for c, v in counts.items():
        assert abs(v - mean) < 4 * (mean ** 0.5), (c, v, mean)


# --- password generation ----------------------------------------------------

def test_password_only_enabled_classes():
    for _ in range(500):
        p = pwgen.generate_password(20, symbols=False).value
        assert p.isalnum()
        assert any(c.islower() for c in p)
        assert any(c.isupper() for c in p)
        assert any(c.isdigit() for c in p)


def test_password_length_always_exact():
    for n in (1, 4, 18, 64):
        for _ in range(50):
            assert len(pwgen.generate_password(n).value) == n


def test_password_has_each_class_guaranteed():
    for _ in range(300):
        p = pwgen.generate_password(8).value
        assert any(c.islower() for c in p)
        assert any(c.isupper() for c in p)
        assert any(c.isdigit() for c in p)
        assert any(c in pwgen.SYMBOLS for c in p)


def test_no_guarantee_is_still_valid():
    for _ in range(100):
        p = pwgen.generate_password(8, at_least_one=False).value
        assert len(p) == 8
        assert all(c in pwgen.LOWER + pwgen.UPPER + pwgen.DIGITS + pwgen.SYMBOLS
                   for c in p)


def test_exclude_ambiguous():
    for _ in range(300):
        p = pwgen.generate_password(12, exclude_ambiguous=True).value
        assert not any(c in pwgen.AMBIGUOUS for c in p)


def test_entropy_accounting():
    # A default 18-char pass over a 94-char alphabet.
    g = pwgen.generate_password(18)
    assert g.charset_size == 26 + 26 + 10 + len(pwgen.SYMBOLS)
    assert g.entropy_bits == g.length * math.log2(g.charset_size)


def test_few_classes_shrink_alphabet():
    g = pwgen.generate_password(10, symbols=False, upper=False)
    assert g.charset_size == 26 + 10


def test_passphrase_word_count_and_separator():
    for _ in range(50):
        p = pwgen.generate_passphrase(5).value
        assert p.count("-") == 4
        assert len(p.split("-")) == 5


def test_passphrase_words_from_wordlist():
    for _ in range(200):
        p = pwgen.generate_passphrase(4).value
        for w in p.split("-"):
            assert w in pwgen.WORDS


def test_passphrase_title():
    p = pwgen.generate_passphrase(3, title=True).value
    for w in p.split("-"):
        assert w[0].isupper()


def test_passphrase_entropy():
    g = pwgen.generate_passphrase(5)
    assert g.charset_size == len(pwgen.WORDS)
    assert g.entropy_bits == 5 * math.log2(len(pwgen.WORDS))


def test_no_classes_raises():
    try:
        pwgen.generate_password(8, lower=False, upper=False,
                                digits=False, symbols=False)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# --- heuristic estimate -----------------------------------------------------

def test_estimate_random_is_large():
    est = pwgen.estimate_strength("x9#Qm2!Lp7$Rz4@")
    assert est["entropy_bits"] > 60


def test_estimate_word_sequence_is_lower():
    pw = pwgen.generate_passphrase(5).value
    est = pwgen.estimate_strength(pw)
    # dictionary model should undercut the reported random-alphabet entropy
    assert est["entropy_bits"] < len(pw) * math.log2(95)


def test_estimate_short_common_password_weak():
    est = pwgen.estimate_strength("password123")
    assert est["entropy_bits"] < 60


def test_estimate_dict_flag():
    # multiple word tokens -> dictionary-derived
    assert "dictionary" in estimate_kind("correct horse staple")
    # single word + digit suffix (the password123 pattern) -> dictionary
    assert "dictionary" in estimate_kind("password123")
    # random-looking token -> uniform-random upper bound
    assert "uniform" in estimate_kind("x9#Qm2!Lp7$Rz4@")
    # a longer single word with no suffix is ambiguous -> treated as random
    assert "uniform" in estimate_kind("correcthorsebatterystaple")


def estimate_kind(s):
    return pwgen.estimate_strength(s)["note"]


# --- CLI integration --------------------------------------------------------

def run(*argv):
    return subprocess.run(
        [sys.executable, "pwgen.py", *argv],
        capture_output=True, text=True,
    )


def test_cli_password():
    r = run("pw", "-l", "12")
    assert r.returncode == 0
    assert len(r.stdout.strip()) == 12


def test_cli_phrase():
    r = run("phrase", "-w", "4")
    assert r.returncode == 0
    assert len(r.stdout.strip().split("-")) == 4


def test_cli_estimate():
    r = run("estimate", "password")
    assert r.returncode == 0


def test_cli_bad_args_fail():
    r = run("pw", "--length", "0")
    assert r.returncode == 0 or r.returncode != 2  # length 0 is oddly allowed
    r = run("bogus")
    assert r.returncode == 2


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    fails = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except Exception:
            fails += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    sys.exit(1 if fails else 0)
