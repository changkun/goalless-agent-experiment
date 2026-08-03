"""Public conversion API."""

from __future__ import annotations

from .parser import parse
from .render import render as _render


def convert(text: str) -> str:
    """Convert a Markdown string to an HTML fragment."""
    return _render(parse(text))
