"""Standalone test runner (no pytest needed)."""

from __future__ import annotations

import sys
import traceback

from fractal_poetry import recite, render
from fractal_poetry.poem import Stanza


def _check(name, fn):
    try:
        fn()
    except Exception:
        print(f"FAIL  {name}")
        traceback.print_exc()
        return False
    print(f"ok    {name}")
    return True


def test_render_smoke():
    out = render(width=20, height=8, max_iter=30)
    lines = out.splitlines()
    assert len(lines) == 8
    for line in lines:
        assert len(line) == 20
    assert " " in out
    assert any(ch in out for ch in ".:-=+*#%@")


def test_render_rejects_tiny():
    for kwargs in ({"width": 2, "height": 10}, {"width": 10, "height": 2},
                   {"width": 10, "height": 10, "max_iter": 2}):
        try:
            render(**kwargs)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {kwargs}")


def test_stanza_is_palindromic():
    s = Stanza(whole="set", property="contains a coast", middle="a coast")
    a, b, c, d, e = s.lines()
    assert a == e and b == d


def test_recite_has_three_stanzas():
    out = recite()
    non_blank = [line for line in out.splitlines() if line.strip()]
    assert len(non_blank) == 15
    for whole in ("set", "year", "poem"):
        assert whole in out


def main() -> int:
    tests = [test_render_smoke, test_render_rejects_tiny,
             test_stanza_is_palindromic, test_recite_has_three_stanzas]
    passed = sum(_check(t.__name__, t) for t in tests)
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
