"""Utility helpers for tokenizing and normalizing raw text."""

from __future__ import annotations

import re
import unicodedata

# Split on any whitespace run, keeping the words/punctuation that appear.
_SPLIT_RE = re.compile(r"\s+")

# Unicode general category "Mn" == nonspacing combining mark (accents etc.).
_COMBINING = unicodedata.combining


def tokenize(text: str) -> list[str]:
    """Split text into whitespace-delimited tokens.

    Newlines and punctuation are preserved as-is on their own tokens so the
    generator can reproduce sentence and paragraph structure.
    """
    return _SPLIT_RE.split(text.strip())


def normalize_unicodedata(text: str) -> str:
    """Normalize to NFKD compatibility form and drop combining marks, so
    accented and compatibility characters reduce to their base ASCII form.

    Case is left untouched. Example: ``"café"`` -> ``"cafe"``, ``"ｆｕｌｌ"``
    -> ``"full"``.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not _COMBINING(ch))
