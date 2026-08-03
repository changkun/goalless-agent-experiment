"""terminal-todo: a tiny, dependency-free terminal task manager."""

__version__ = "1.0.0"

from .store import Store, TodoError  # noqa: F401

__all__ = ["Store", "TodoError", "__version__"]
