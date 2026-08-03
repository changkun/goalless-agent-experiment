"""A small terminal Wordle clone."""

from .logic import evaluate, pick_word
from .words import WORDS

__all__ = ["WORDS", "evaluate", "pick_word"]
__version__ = "0.1.0"
