"""A small, dependency-free Markdown subset to HTML converter.

Supports:
  - ATX headings (# .. ######)
  - unordered lists (-, *, +) with nesting
  - ordered lists (1. ...)
  - blockquotes (>)
  - fenced code blocks (```)
  - inline code, bold, italic, links, and images
  - blank-line separated paragraphs, line breaks
"""
from __future__ import annotations

import re

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BLOCKQUOTE = re.compile(r"^>\s?(.*)$")
_FENCE = re.compile(r"^```([\w+-]*)")
_UNORDERED_ITEM = re.compile(r"^([ \t]*)[-*+]\s+(.*)$")
_ORDERED_ITEM = re.compile(r"^([ \t]*)\d+\.\s+(.*)$")

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _inline(text: str) -> str:
    text = _escape(text)
    text = _IMAGE.sub(r'<img src="\2" alt="\1" />', text)
    text = _LINK.sub(r'<a href="\2">\1</a>', text)
    text = _INLINE_CODE.sub(r"<code>\1</code>", text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    return text


def _indent_level(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _parse_list(lines: list[str], start: int, ordered: bool) -> tuple[str, int]:
    tag = "ol" if ordered else "ul"
    pattern = _ORDERED_ITEM if ordered else _UNORDERED_ITEM
    html = [f"<{tag}>"]
    stack: list[tuple[str, int]] = [(tag, 0)]

    def close_to(level: int) -> None:
        while len(stack) > 1 and stack[-1][1] > level:
            tag, _ = stack.pop()
            html.append(f"</{tag}>")

    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        match = pattern.match(line)
        if not match:
            break
        level = _indent_level(line) // 2
        content = match.group(2)
        if level > stack[-1][1]:
            new_tag = "ul" if not ordered else "ul"
            html.append(f"<{new_tag}>")
            stack.append((new_tag, level))
        elif level < stack[-1][1]:
            close_to(level)
        html.append(f"<li>{_inline(content)}</li>")
        i += 1

    while len(stack) > 1:
        tag, _ = stack.pop()
        html.append(f"</{tag}>")
    html.append(f"</{tag}>")
    return "\n".join(html), i


def to_html(markdown: str) -> str:
    if markdown is None:
        return ""
    lines = markdown.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.rstrip()

        if not stripped.strip():
            i += 1
            continue

        heading = _HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        fence = _FENCE.match(stripped)
        if fence:
            lang = fence.group(1)
            i += 1
            code_lines: list[str] = []
            while i < n and not _FENCE.match(lines[i].rstrip()):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            data_lang = f' class="language-{lang}"' if lang else ""
            body = _escape("\n".join(code_lines))
            out.append(f"<pre><code{data_lang}>{body}</code></pre>")
            continue

        blockquote = _BLOCKQUOTE.match(stripped)
        if blockquote:
            q_lines: list[str] = []
            while i < n:
                m = _BLOCKQUOTE.match(lines[i])
                if not m:
                    break
                q_lines.append(m.group(1))
                i += 1
            inner = to_html("\n".join(q_lines))
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        unordered = _UNORDERED_ITEM.match(stripped)
        ordered = _ORDERED_ITEM.match(stripped) if not unordered else None
        if unordered:
            html, i = _parse_list(lines, i, ordered=False)
            out.append(html)
            continue
        if ordered:
            html, i = _parse_list(lines, i, ordered=True)
            out.append(html)
            continue

        # Paragraph: consume until a blank line or a block-starter.
        para: list[str] = []
        while i < n:
            current = lines[i]
            if not current.strip():
                break
            if _HEADING.match(current.rstrip()) or _FENCE.match(current.rstrip()):
                break
            para.append(current)
            i += 1
        rendered = " ".join(p.strip() for p in para)
        out.append(f"<p>{_inline(rendered)}</p>")

    return "\n".join(out)
