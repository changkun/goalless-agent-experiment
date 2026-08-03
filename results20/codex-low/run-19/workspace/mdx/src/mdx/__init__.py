"""mdx - a tiny, dependency-free Markdown -> HTML converter and site builder."""

from .parser import convert, render_html

__version__ = "0.1.0"
__all__ = ["convert", "render_html"]
