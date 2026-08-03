"""Pocket: a tiny, dependency-free notes and tasks manager in Markdown."""

from . import core
from .core import Note, add, list_items, read, remove, set_done

__all__ = ["core", "Note", "add", "list_items", "read", "remove", "set_done"]
__version__ = "0.1.0"
