"""A small, dependency-free Markdown parser.

Supports headings, unordered/ordered lists, code blocks (fenced), inline
code, bold, italic, links, images, blockquotes, horizontal rules, and
escaped characters. Raw HTML is passed through untouched.
"""

from __future__ import annotations

import re

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_HR = re.compile(r"^\s*(?:(\*){3,}|(-){3,}|(_){3,})\s*$")
_OL = re.compile(r"^(\d+)[.)]\s+(.*)$")
_UL = re.compile(r"^[-*+]\s+(.*)$")
_FENCE = re.compile(r"^(`{3,}|~{3,})\s*([\w+-]*)")
_BLOCKQUOTE = re.compile(r"^>\s?(.*)$")


def _escape_text(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_attr(text: str) -> str:
    return _escape_text(text).replace('"', "&quot;")


_INLINE_TOKEN = re.compile(
    r"(?P<code>`+)(?P<code_body>.+?)(?P=code)"                              # inline code
    r"|(?P<bold>\*\*|__)(?P<bold_body>.+?)(?P=bold)"                       # bold
    r"|(?P<ital>\*|_)(?P<ital_body>.+?)(?P=ital)"                           # italic
    r"|!\[(?P<img_alt>[^\]]*)\]\((?P<img_src>[^)\s]+)(?:\s+\"(?P<img_title>[^\"]*)\")?\)"  # image
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_href>[^)\s]+)(?:\s+\"(?P<link_title>[^\"]*)\")?\)"  # link
    r"|\\(?P<esc>[\\`*_{}\[\]()#+\-.!])"                              # escaped char
)


def _render_inline(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _INLINE_TOKEN.finditer(text):
        out.append(_escape_text(text[pos : m.start()]))
        if m.group("code_body") is not None:
            out.append(f"<code>{_escape_text(m.group('code_body'))}</code>")
        elif m.group("bold_body") is not None:
            out.append(f"<strong>{_render_inline(m.group('bold_body'))}</strong>")
        elif m.group("ital_body") is not None:
            out.append(f"<em>{_render_inline(m.group('ital_body'))}</em>")
        elif m.group("img_src") is not None:
            alt = _escape_attr(m.group("img_alt"))
            src = _escape_attr(m.group("img_src"))
            title = _escape_attr(m.group("img_title")) if m.group("img_title") else ""
            title_attr = f' title="{title}"' if title else ""
            out.append(f'<img src="{src}" alt="{alt}"{title_attr} />')
        elif m.group("link_href") is not None:
            inner = _render_inline(m.group("link_text"))
            href = _escape_attr(m.group("link_href"))
            title = _escape_attr(m.group("link_title")) if m.group("link_title") else ""
            title_attr = f' title="{title}"' if title else ""
            out.append(f'<a href="{href}"{title_attr}>{inner}</a>')
        else:  # escaped char
            out.append(m.group("esc"))
        pos = m.end()
    out.append(_escape_text(text[pos:]))
    return "".join(out)


def _parse_blocks(lines: list[str]) -> list[tuple[str, str]]:
    """Return a list of (kind, content) block tuples.

    kinds: heading, paragraph, code, blockquote, ul, ol, hr, html
    """
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(lines)
    first_paragraph = True

    while i < n:
        line = lines[i]

        if not line.strip():
            first_paragraph = False
            i += 1
            continue

        # Fenced code block
        fm = _FENCE.match(line)
        if fm:
            fence, lang = fm.group(1), fm.group(2)
            i += 1
            body: list[str] = []
            while i < n and not lines[i].strip().startswith(fence):
                body.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            blocks.append(("code", body))
            continue

        # HTML block (simplistic: a line starting with a tag)
        if line.lstrip().startswith("<"):
            html: list[str] = [line]
            i += 1
            while i < n and lines[i].lstrip() and not lines[i].lstrip().startswith("<") and not _FENCE.match(lines[i]):
                html.append(lines[i])
                i += 1
            blocks.append(("html", html))
            continue

        # Heading
        hm = _HEADING.match(line)
        if hm:
            level = len(hm.group(1))
            blocks.append(("heading", (_render_inline(hm.group(2)), level)))
            first_paragraph = False
            i += 1
            continue

        # Horizontal rule
        if _HR.match(line):
            blocks.append(("hr", ""))
            first_paragraph = False
            i += 1
            continue

        # Blockquote
        if _BLOCKQUOTE.match(line):
            quoted: list[str] = []
            while i < n and _BLOCKQUOTE.match(lines[i]):
                inner = _BLOCKQUOTE.match(lines[i]).group(1)
                quoted.append(inner)
                i += 1
            blocks.append(("blockquote", quoted))
            first_paragraph = False
            continue

        # Lists
        um = _UL.match(line)
        om = _OL.match(line)
        if um or om:
            ordered = bool(om)
            items: list[tuple[str, str]] = []
            if om:
                items.append((om.group(1), om.group(2)))
                i += 1
                while i < n:
                    m2 = _OL.match(lines[i])
                    m1 = _UL.match(lines[i])
                    if m2:
                        items.append((m2.group(1), m2.group(2)))
                        i += 1
                    elif m1:
                        items.append((m1.group(1), m1.group(2)))
                        i += 1
                    else:
                        break
            else:
                items.append(("", um.group(1)))
                i += 1
                while i < n:
                    m1 = _UL.match(lines[i])
                    if m1:
                        items.append(("", m1.group(1)))
                    else:
                        break
                    i += 1
            blocks.append(("ol" if ordered else "ul", items))
            first_paragraph = False
            continue

        # Paragraph: accumulate consecutive lines (loose wrapping)
        para: list[str] = [line.strip()]
        i += 1
        while i < n and lines[i].strip():
            para.append(lines[i].strip())
            i += 1
        blocks.append(("paragraph", (para, first_paragraph)))
        first_paragraph = False

    return blocks



def _render_block(block: tuple[str, str]) -> str:
    kind, content = block
    if kind == "paragraph":
        lines, first = content
        text = " ".join(lines)
        rendered = _render_inline(text)
        if first:
            return f"<p class=\"lead\">{rendered}</p>"
        return f"<p>{rendered}</p>"
    if kind == "heading":
        text, level = content
        return f"<h{level}>{text}</h{level}>"
    if kind == "code":
        body = "\n".join(content)
        return f"<pre><code>{_escape_text(body)}</code></pre>"
    if kind == "blockquote":
        quoted = [_render_inline(l) for l in content]
        return f"<blockquote>{''.join(f'<p>{t}</p>' for t in quoted)}</blockquote>"
    if kind == "ul":
        items = "".join(f"<li>{_render_inline(text)}</li>" for _, text in content)
        return f"<ul>{items}</ul>"
    if kind == "ol":
        items = "".join(f"<li>{_render_inline(text)}</li>" for _, text in content)
        return f"<ol>{items}</ol>"
    if kind == "hr":
        return "<hr />"
    if kind == "html":
        return "".join(content)
    return ""


def convert(text: str) -> str:
    """Convert Markdown text to an HTML fragment."""
    lines = text.splitlines()
    blocks = _parse_blocks(lines)
    return "\n".join(_render_block(b) for b in blocks)


def render_html(title: str, body: str, lang: str = "en") -> str:
    """Wrap a rendered body in a complete HTML document."""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape_attr(title)}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 42rem; margin: 3rem auto; line-height: 1.6; padding: 0 1rem; }}
    .lead {{ font-size: 1.15rem; color: #444; }}
    pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; }}
    blockquote {{ border-left: 3px solid #ccc; margin-left: 0; padding-left: 1rem; color: #555; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
