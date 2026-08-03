"""A small Markdown-to-HTML converter supporting a practical subset of syntax."""

import re
from html import escape

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^```(\w*)\s*$")
_LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
_BLOCKQUOTE = re.compile(r"^>\s?(.*)$")
_HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")

_INLINE = [
    (re.compile(r"`([^`]+)`"), lambda m: "<code>" + escape(m.group(1)) + "</code>"),
    (
        re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"),
        lambda m: f'<a href="{escape(m.group(2), quote=True)}">{m.group(1)}</a>',
    ),
    (re.compile(r"\*\*([^*]+)\*\*"), lambda m: "<strong>" + m.group(1) + "</strong>"),
    (re.compile(r"__([^_]+)__"), lambda m: "<strong>" + m.group(1) + "</strong>"),
    (re.compile(r"\*([^*\s][^*]*)\*"), lambda m: "<em>" + m.group(1) + "</em>"),
    (re.compile(r"_([^_\s][^_]*)_"), lambda m: "<em>" + m.group(1) + "</em>"),
]


def _inline(text: str) -> str:
    text = escape(text)
    for pattern, repl in _INLINE:
        text = pattern.sub(repl, text)
    return text


def _paragraph(text: str) -> str:
    return f"<p>{_inline(text)}</p>"


def _code_block(lang: str, body: str) -> str:
    cls = f' class="language-{escape(lang)}"' if lang else ""
    return f"<pre><code{cls}>{escape(body)}</code></pre>"


def _list_block(ordered: bool, items: list) -> str:
    tag = "ol" if ordered else "ul"
    lis = "".join(f"<li>{_inline(i)}</li>" for i in items)
    return f"<{tag}>{lis}</{tag}>"


def extract_title(text: str) -> str | None:
    """Return the first H1 heading text, or None."""
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 1:
            return m.group(2).strip()
    return None


def markdown(text: str) -> str:
    """Convert Markdown text to an HTML fragment."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    list_buffer: list[tuple[bool, list[str]]] = []

    def flush_lists() -> None:
        for ordered, items in list_buffer:
            out.append(_list_block(ordered, items))
        list_buffer.clear()

    while i < n:
        line = lines[i].rstrip()

        # Fenced code block
        fence = _FENCE.match(line)
        if fence:
            flush_lists()
            lang = fence.group(1)
            body: list[str] = []
            i += 1
            while i < n and not _FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(_code_block(lang, "\n".join(body)))
            continue

        # Horizontal rule
        if _HR.match(line):
            flush_lists()
            out.append("<hr>")
            i += 1
            continue

        # Heading
        heading = _HEADING.match(line)
        if heading:
            flush_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        # Blockquote (gather consecutive lines)
        if line.startswith(">"):
            flush_lists()
            quote = [line.lstrip(">").strip()]
            i += 1
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(q for q in quote if q))}</blockquote>")
            continue

        # List item
        item = _LIST_ITEM.match(line)
        if item:
            bullet = item.group(2)
            ordered = bool(re.match(r"\d+\.", bullet))
            text = item.group(3)
            if list_buffer and list_buffer[-1][0] != ordered:
                flush_lists()
            if not list_buffer or list_buffer[-1][0] != ordered:
                list_buffer.append((ordered, []))
            list_buffer[-1][1].append(text)
            i += 1
            continue

        # Blank line separator
        if not line.strip():
            flush_lists()
            i += 1
            continue

        # Paragraph - gather until blank line
        flush_lists()
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not _HEADING.match(lines[i]) \
                and not _FENCE.match(lines[i]) and not _LIST_ITEM.match(lines[i]) \
                and not lines[i].startswith(">") and not _HR.match(lines[i]):
            para.append(lines[i])
            i += 1
        out.append(_paragraph(" ".join(p.strip() for p in para)))

    flush_lists()
    return "\n".join(out)
