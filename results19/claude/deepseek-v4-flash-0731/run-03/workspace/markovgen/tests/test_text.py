from __future__ import annotations

from markovgen.text import normalize_unicodedata


def test_normalize_strips_combining_marks():
    assert normalize_unicodedata("café") == "cafe"


def test_normalize_compatibility_characters():
    assert normalize_unicodedata("ｆｕｌｌ") == "full"
