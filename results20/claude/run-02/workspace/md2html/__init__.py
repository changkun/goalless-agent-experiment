"""md2html — a dependency-free Markdown to HTML converter.

A small but honest CommonMark-flavored converter built with the Python
standard library only. Supports the everyday block and inline constructs:
headings, paragraphs, blockquotes, fenced and indented code blocks, ordered
and unordered lists (nested), thematic breaks, and inline emphasis, strong,
code, links, and images. Unknown characters are HTML-escaped by default.
"""

from .convert import convert

__all__ = ["convert"]
__version__ = "1.0.0"
