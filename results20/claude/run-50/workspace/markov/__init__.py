"""MarkovText: a small, dependency-free Markov chain text generator."""

from .core import MarkovModel, train_on_text, train_on_file

__all__ = ["MarkovModel", "train_on_text", "train_on_file"]
__version__ = "0.1.0"
