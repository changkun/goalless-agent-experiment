"""pagepress - a minimal, dependency-free static site generator."""

from .md import markdown, extract_title
from .cli import main

__version__ = "0.1.0"
__all__ = ["markdown", "extract_title", "main", "__version__"]
