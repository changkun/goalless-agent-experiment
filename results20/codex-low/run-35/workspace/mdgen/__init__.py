"""mdgen - a tiny, dependency-free Markdown to static HTML site generator."""

from .parser import ParseError, render_html, render_markdown

__all__ = ["ParseError", "render_html", "render_markdown"]
__version__ = "0.1.0"
