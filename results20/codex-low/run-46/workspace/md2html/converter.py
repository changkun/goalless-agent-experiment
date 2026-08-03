"""A small, dependency-free Markdown to HTML converter."""

from __future__ import annotations

import html
import re
from typing import List, Match, Optional


def _image(m: Match) -> str:
    alt = m.group(1)
    src = m.group(2)
    title = m.group(3)
    title_attr = f' title="{title}"' if title else ""
    return f'<img src="{src}" alt="{alt}"{title_attr}>'


def _link(m: Match) -> str:
    text = m.group(1)
    href = m.group(2)
    title = m.group(3)
    title_attr = f' title="{title}"' if title else ""
    return f'<a href="{href}"{title_attr}>{text}</a>'


def _render_inline(text: str) -> str:
    """Apply inline Markdown (emphasis, code, links, images) to one line.

    The input is escaped once up front, so ``&``, ``<`` and ``>`` in user
    content can never escape into markup. Link/image attribute captures come
    from this already-escaped text and are used as-is.
    """
    escaped = html.escape(text, quote=False)
    patterns = [
        (re.compile(r"\*\*(.+?)\*\*"), lambda m: f"<strong>{m.group(1)}</strong>"),
        (re.compile(r"__(.+?)__"), lambda m: f"<strong>{m.group(1)}</strong>"),
        (re.compile(r"(?<![*])\*([^*\n]+?)\*(?!\*)"), lambda m: f"<em>{m.group(1)}</em>"),
        (re.compile(r"(?<!_)_([^_\n]+?)_(?!_)"), lambda m: f"<em>{m.group(1)}</em>"),
        (re.compile(r"`([^`\n]+?)`"), lambda m: f"<code>{m.group(1)}</code>"),
        (re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]+?)\")?\)"), _image),
        (re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]+?)\")?\)"), _link),
    ]
    for pattern, repl in patterns:
        escaped = pattern.sub(repl, escaped)
    return escaped


_BLOCKQUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_UL_RE = re.compile(r"^\s*[-+*]\s+(.*)$")
_OL_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR_RE = re.compile(r"^\s*(?:\*{3,}|-{3,}|_{3,})\s*$")
_FENCE_RE = re.compile(r"^```(\w*)$")


def _join_lines(lines: List[str]) -> str:
    return "<br>".join(_render_inline(line) for line in lines)


def convert(markdown: str) -> str:
    """Convert Markdown text to an HTML fragment.

    Args:
        markdown: The Markdown source as a string.

    Returns:
        An HTML fragment (no <html>/<body> wrapper).
    """
    if not isinstance(markdown, str):
        raise TypeError("markdown must be a string")

    lines = markdown.splitlines()
    out: List[str] = []

    para: List[str] = []
    list_items: List[str] = []
    list_tag: Optional[str] = None
    quote: List[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{_join_lines(para)}</p>")
            para.clear()

    def flush_list() -> None:
        nonlocal list_tag
        if list_items:
            items = "".join(
                f"<li>{_render_inline(item)}</li>" for item in list_items
            )
            out.append(f"<{list_tag}>{items}</{list_tag}>")
            list_items.clear()

    def flush_quote() -> None:
        if quote:
            inner = convert("\n".join(quote))
            out.append(f"<blockquote>{inner}</blockquote>")
            quote.clear()

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        fence = _FENCE_RE.match(line)
        if fence:
            flush_para()
            flush_list()
            quote.clear()
            lang = html.escape(fence.group(1), quote=True)
            code: List[str] = []
            i += 1
            while i < n and not _FENCE_RE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            body = html.escape("\n".join(code))
            lang_attr = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{lang_attr}>{body}</code></pre>")
            continue

        if not line.strip():
            flush_para()
            flush_list()
            flush_quote()
            list_tag = None
            i += 1
            continue

        bq = _BLOCKQUOTE_RE.match(line)
        if bq:
            flush_para()
            flush_list()
            list_tag = None
            quote.append(bq.group(1))
            i += 1
            continue
        if quote:
            flush_quote()

        if _HR_RE.match(line):
            flush_para()
            flush_list()
            list_tag = None
            out.append("<hr>")
            i += 1
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            flush_para()
            flush_list()
            list_tag = None
            level = len(heading.group(1))
            out.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        ul = _UL_RE.match(line)
        ol = _OL_RE.match(line)
        if ul or ol:
            flush_para()
            item_content = (ul or ol).group(1)
            tag = "ul" if ul else "ol"
            if tag != list_tag:
                flush_list()
                list_tag = tag
            list_items.append(item_content)
            i += 1
            continue
        if list_items:
            flush_list()
            list_tag = None

        para.append(line)
        i += 1

    flush_para()
    flush_list()
    flush_quote()
    return "\n".join(out)
