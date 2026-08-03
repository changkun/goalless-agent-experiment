"""HTML rendering for the block tree produced by `parser.parse`.

Block nodes are rendered by `render_block`; text is processed by
`render_inline`, a tokenizer that walks the source left to right and never
re-processes its own output (so an autolink never fires inside the attribute
of a link we just generated).
"""

from __future__ import annotations

import re
from html import escape

from .parser import (Heading, Paragraph, CodeBlock, Hr,
                     Blockquote, ListItem, ListBlock)

# --- regexes ---------------------------------------------------------------

# Inline code span: backtick-delimited, closing run of equal length.
CODE_SPAN = re.compile(r"(`+)([^`]*?)\1")

# Link/image: ![alt](src) / [label](dest "title")
IMG = re.compile(r"!\[([^\[\]]*)\]\(\s*([^)\s]+)\s*(?:\"([^\"]*)\")?\s*\)")
LINK = re.compile(r"\[([^\[\]]*)\]\(\s*([^)\s]+)\s*(?:\"([^\"]*)\")?\s*\)")

# Bare URL for autolinking (scheme://... upto trailing punctuation).
AUTOLINK = re.compile(r"https?://[^\s<>\"']+[A-Za-z0-9/]")


def render(blocks) -> str:
    out = "\n\n".join(render_block(b) for b in blocks)
    return out.rstrip() + "\n"


def render_block(block) -> str:
    if isinstance(block, Heading):
        return f"<h{block.level}>{render_inline(block.text)}</h{block.level}>"
    if isinstance(block, Paragraph):
        return "<p>" + render_inline(" ".join(block.lines)) + "</p>"
    if isinstance(block, CodeBlock):
        if block.info:
            cls = f' class="language-{escape(block.info.split()[0])}"'
        else:
            cls = ""
        return f"<pre><code{cls}>{escape(block.code)}</code></pre>"
    if isinstance(block, Hr):
        return "<hr>"
    if isinstance(block, Blockquote):
        inner = "\n".join(render_block(c) for c in block.children)
        return f"<blockquote>\n{inner}\n</blockquote>"
    if isinstance(block, ListBlock):
        tag = "ol" if block.ordered else "ul"
        items = "\n".join(f"<li>{_render_item(li)}</li>" for li in block.items)
        return f"<{tag}>\n{items}\n</{tag}>"
    raise TypeError(f"unknown block: {block!r}")


def _render_item(li: ListItem) -> str:
    return "\n".join(render_block(c) for c in li.children)


# --- inline tokenizer ------------------------------------------------------

def render_inline(text: str) -> str:
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]

        # inline code span
        if ch == "`":
            m = CODE_SPAN.match(text, i)
            if m:
                out.append(f"<code>{escape(m.group(2))}</code>")
                i = m.end()
                continue

        # image
        if ch == "!" and i + 1 < n and text[i + 1] == "[":
            m = IMG.match(text, i)
            if m:
                out.append(_sub_img(m))
                i = m.end()
                continue

        # link
        if ch == "[":
            m = LINK.match(text, i)
            if m:
                out.append(_sub_link(m))
                i = m.end()
                continue

        # strong (** or __) must be tried before emphasis
        if ch == "*" or ch == "_":
            # triple marker: ***x*** -> <strong><em>x</em></strong>
            marker3 = ch * 3
            if text.startswith(marker3, i):
                run = _find_closer(text, i + 3, marker3)
                if run is not None:
                    inner = text[i + 3:run]
                    out.append(f"<strong><em>{render_inline(inner)}</em></strong>")
                    i = run + 3
                    continue
            marker = ch * 2
            if text.startswith(marker, i):
                run = _find_closer(text, i + 2, marker)
                if run is not None:
                    inner = text[i + 2:run]
                    out.append(f"<strong>{render_inline(inner)}</strong>")
                    i = run + 2
                    continue
            # single emphasis
            run = _find_closer(text, i + 1, ch)
            if run is not None and run > i + 1:
                inner = text[i + 1:run]
                if inner.strip():
                    out.append(f"<em>{render_inline(inner)}</em>")
                    i = run + 1
                    continue

        # bare URL autolink
        m = AUTOLINK.match(text, i)
        if m:
            url = m.group(0)
            # only autolink if it's not glued to a word char before
            if i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "._/"):
                out.append(f'<a href="{escape(url, quote=True)}">{escape(url)}</a>')
                i = m.end()
                continue

        # literal character with escaping
        out.append(_escape_char(ch))
        i += 1

    return "".join(out)


def _find_closer(text: str, start: int, marker: str) -> int:
    """Return the index of the next occurrence of `marker`, or None."""
    return text.find(marker, start)


def _escape_char(ch: str) -> str:
    if ch == "&":
        return "&amp;"
    if ch == "<":
        return "&lt;"
    if ch == ">":
        return "&gt;"
    if ch == '"':
        return "&quot;"
    return ch


def _sub_img(m) -> str:
    src = escape(m.group(2), quote=True)
    alt = escape(m.group(1), quote=True)
    out = f'<img src="{src}" alt="{alt}"'
    if m.group(3):
        out += f' title="{escape(m.group(3), quote=True)}"'
    out += ">"
    return out


def _sub_link(m) -> str:
    dest = escape(m.group(2), quote=True)
    out = f'<a href="{dest}"'
    if m.group(3):
        out += f' title="{escape(m.group(3), quote=True)}"'
    out += ">" + render_inline(m.group(1)) + "</a>"
    return out
