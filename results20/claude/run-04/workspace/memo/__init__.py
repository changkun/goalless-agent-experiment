"""Memo — a tiny, zero-dependency, tagged journal stored as JSON."""

from .core import MemoStore, MemoError

__all__ = ["MemoStore", "MemoError"]
__version__ = "0.1.0"
