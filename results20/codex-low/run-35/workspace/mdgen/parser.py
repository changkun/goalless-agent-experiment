"""A small, dependency-free CommonMark-ish Markdown parser.

Supports ATX headings, paragraphs, ordered/unordered lists, fenced code
blocks, blockquotes, horizontal rules, and inline bold, italic, code, links,
and images. The output is a fully static HTML snippet.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import quote


class ParseError(Exception):
    """Raised when the Markdown source cannot be parsed."""


_BLOCKQUOTE = re.compile(r"^ *>\s?(.*)$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^ *(`{3,}|~{3,})\s*([\w+-]*)\s*$")
_HR = re.compile(r"^ *([-*_])( *\1){2,} *$")
_UL = re.compile(r"^ *([-*+])\s+(.*)$")
_OL = re.compile(r"^ *(\d+)[.)]\s+(.*)$")

_INLINE_CODE = re.compile(r"`([^`]*)`")
_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)")


def _escape_url(url: str) -> str:
    return quote(url, safe="/:#?&=@%+~,;")


def _render_inline(text: str) -> str:
    """Render inline Markdown constructs into escaped HTML.

    Links and images are resolved before HTML escaping so that URLs and
    titles can carry their own quoting; the substituted HTML is stashed in
    placeholders that survive the subsequent escaping pass.
    """
    placeholders: list[str] = []

    def stash(item: str) -> str:
        placeholders.append(item)
        return f"\x00{len(placeholders) - 1}\x00"

    def img(match: re.Match) -> str:
        alt = html.escape(match.group(1))
        src = _escape_url(match.group(2))
        title = match.group(3)
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return stash(f'<img src="{src}" alt="{alt}"{title_attr} />')

    def link(match: re.Match) -> str:
        label = html.escape(match.group(1))
        href = _escape_url(match.group(2))
        return stash(f'<a href="{href}">{label}</a>')

    text = _IMG.sub(img, text)
    text = _LINK.sub(link, text)
    text = html.escape(text, quote=False)

    def code(match: re.Match) -> str:
        return "<code>" + match.group(1) + "</code>"

    def bold(match: re.Match) -> str:
        return "<strong>" + (match.group(1) or match.group(2)) + "</strong>"

    def italic(match: re.Match) -> str:
        return "<em>" + (match.group(1) or match.group(2)) + "</em>"

    text = _INLINE_CODE.sub(code, text)
    text = _BOLD.sub(bold, text)
    text = _ITALIC.sub(italic, text)

    def restore(match: re.Match) -> str:
        return placeholders[int(match.group(1))]

    return re.sub(r"\x00(\d+)\x00", restore, text)


@dataclass
class _Block:
    kind: str
    value: str
    lang: str = ""
    ordered: bool = False
    level: int = 1


def _parse_blocks(lines: list[str]) -> list[_Block]:
    blocks: list[_Block] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        fenced = _FENCE.match(line)
        if fenced:
            marker = fenced.group(1)
            lang = fenced.group(2)
            i += 1
            buf = []
            while i < n:
                stripped = lines[i].lstrip()
                if stripped.startswith(marker) and not stripped.lstrip("`~").strip():
                    i += 1
                    break
                buf.append(lines[i])
                i += 1
            blocks.append(_Block("code", "\n".join(buf), lang=lang))
            continue

        heading = _HEADING.match(line)
        if heading:
            blocks.append(_Block("heading", heading.group(2), level=len(heading.group(1))))
            i += 1
            continue

        if _HR.match(line):
            blocks.append(_Block("hr", ""))
            i += 1
            continue

        quote = _BLOCKQUOTE.match(line)
        if quote:
            buf = []
            while i < n and _BLOCKQUOTE.match(lines[i]):
                buf.append(_BLOCKQUOTE.match(lines[i]).group(1))
                i += 1
            blocks.append(_Block("blockquote", _render_inline("\n".join(buf))))
            continue

        ul = _UL.match(line)
        ol = _OL.match(line)
        if ul or ol:
            items: list[tuple[bool, str]] = []
            while i < n and lines[i].strip():
                mu = _UL.match(lines[i])
                mo = _OL.match(lines[i])
                if mu or mo:
                    items.append((bool(mo), (mu or mo).group(2)))
                    i += 1
                else:
                    break
            blocks.append(_Block("list", "", ordered=bool(ol)))
            for is_ol, item in items:
                blocks.append(_Block("item", item, ordered=is_ol))
            continue

        buf = []
        while i < n and lines[i].strip():
            if (_HEADING.match(lines[i]) or _FENCE.match(lines[i])
                    or _HR.match(lines[i]) or _UL.match(lines[i])
                    or _OL.match(lines[i]) or _BLOCKQUOTE.match(lines[i])):
                break
            buf.append(lines[i].strip())
            i += 1
        blocks.append(_Block("paragraph", " ".join(buf)))

    return blocks


def _render_blocks(blocks: list[_Block]) -> str:
    out: list[str] = []
    in_list = False
    list_ordered = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ol>" if list_ordered else "</ul>")
            in_list = False

    for block in blocks:
        if block.kind == "heading":
            close_list()
            out.append(f"<h{block.level}>{_render_inline(block.value)}</h{block.level}>")
        elif block.kind == "paragraph":
            close_list()
            out.append(f"<p>{_render_inline(block.value)}</p>")
        elif block.kind == "code":
            close_list()
            lang = f' class="language-{html.escape(block.lang)}"' if block.lang else ""
            out.append(f"<pre><code{lang}>{html.escape(block.value)}</code></pre>")
        elif block.kind == "hr":
            close_list()
            out.append("<hr />")
        elif block.kind == "blockquote":
            close_list()
            out.append(f"<blockquote>{block.value}</blockquote>")
        elif block.kind == "list":
            close_list()
            out.append("<ol>" if block.ordered else "<ul>")
            in_list = True
            list_ordered = block.ordered
        elif block.kind == "item":
            if not in_list:
                out.append("<ol>" if block.ordered else "<ul>")
                in_list = True
                list_ordered = block.ordered
            out.append(f"<li>{_render_inline(block.value)}</li>")

    close_list()
    return "\n".join(out)


def render_markdown(text: str) -> str:
    """Convert raw Markdown text to an HTML snippet (no <html> wrapper)."""
    if not isinstance(text, str):
        raise ParseError("Markdown source must be a string")
    return _render_blocks(_parse_blocks(text.splitlines()))


def render_html(text: str, title: str = "Site") -> str:
    """Render Markdown into a complete standalone HTML page with a theme."""
    body = render_markdown(text)
    safe = html.escape(title)
    css = """
:root { --bg:#fafafa; --fg:#1f2328; --muted:#57606a; --accent:#0969da;
        --border:#d0d7de; --code-bg:#f6f8fa; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff;
          --border:#30363d; --code-bg:#161b22; }
}
* { box-sizing:border-box; }
body { margin:0; line-height:1.6; color:var(--fg); background:var(--bg);
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
main { max-width:760px; margin:0 auto; padding:2.5rem 1.25rem 4rem; }
h1,h2,h3,h4 { line-height:1.25; margin:1.6em 0 .6em; }
h1 { border-bottom:1px solid var(--border); padding-bottom:.3em; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
code { background:var(--code-bg); border-radius:6px; padding:.15em .35em;
       font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:.9em; }
pre { background:var(--code-bg); border:1px solid var(--border); border-radius:8px;
      padding:1em; overflow-x:auto; }
pre code { background:none; padding:0; }
blockquote { margin:1em 0; padding:.1em 1em; border-left:4px solid var(--accent); color:var(--muted); }
hr { border:0; border-top:1px solid var(--border); margin:2em 0; }
li + li { margin-top:.25em; }
""".strip()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{safe}</title>
<style>
{css}
</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""
