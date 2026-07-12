"""Tests for the fractal poetry package."""

from fractal_poetry import recite, render
from fractal_poetry.poem import Stanza


def test_render_smoke() -> None:
    out = render(width=20, height=8, max_iter=30)
    lines = out.splitlines()
    assert len(lines) == 8
    for line in lines:
        assert len(line) == 20
    # At least one of every kind of char should appear in a real render.
    assert " " in out  # interior of the set
    assert any(ch in out for ch in ".:-=+*#%@")  # escape ramp shows up


def test_render_rejects_tiny() -> None:
    import pytest
    with pytest.raises(ValueError):
        render(width=2, height=10)
    with pytest.raises(ValueError):
        render(width=10, height=2)
    with pytest.raises(ValueError):
        render(width=10, height=10, max_iter=2)


def test_stanza_is_palindromic() -> None:
    s = Stanza(whole="set", property="contains a coast", middle="a coast")
    a, b, c, d, e = s.lines()
    assert a == e
    assert b == d


def test_recite_has_three_stanzas() -> None:
    out = recite()
    # Each stanza is 5 non-blank lines plus 1 blank separator (except last).
    non_blank = [line for line in out.splitlines() if line.strip()]
    assert len(non_blank) == 15
    # The three 'wholes' should each appear.
    assert "set" in out
    assert "year" in out
    assert "poem" in out
