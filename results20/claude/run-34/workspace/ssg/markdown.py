"""A small, dependency-free Markdown -> HTML converter.

Not a full CommonMark implementation -- it covers the subset used by
personal blogs and docs sites: ATX headings, paragraphs, fenced code
blocks, ordered/unordered lists, blockquotes, horizontal rules, tables,
and the common inline styles (bold, italic, code, links, images).

Deliberately simple so the entire file is readable in one sitting.
"""

from __future__ import annotations

import html
import re
from typing import List, Tuple

# --- block-level helpers ---------------------------------------------------

def _is_fence(line: str) -> bool:
    s = line.strip()
    return s.startswith("```") or s.startswith("~~~")


def _is_hr(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    return bool(re.fullmatch(r"(\s*[-*_]\s*){3,}", s)) and len(set(s.replace(" ", ""))) == 1


def _is_heading(line: str) -> Tuple[int, str] | None:
    m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
    if m:
        return len(m.group(1)), m.group(2)
    return None


def _is_list_marker(line: str) -> Tuple[str, str] | None:
    """Return (kind, rest) where kind is 'ul' or 'ol'."""
    m = re.match(r"^\s*([-+*])\s+(.*)", line)
    if m:
        return "ul", m.group(2)
    m = re.match(r"^\s*(\d+[.)])\s+(.*)", line)
    if m:
        return "ol", m.group(2)
    return None


def _is_table_row(line: str) -> bool:
    return "|" in line


def _parse_table_row(row: str) -> List[str]:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells


def _is_table_sep(row: str) -> bool:
    cells = _parse_table_row(row)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


# --- inline parsing ---------------------------------------------------------

def _inline(text: str) -> str:
    """Convert inline markdown to HTML within a single-line-ish string."""
    # Escape first, then apply patterns that insert their own tags.
    text = html.escape(text, quote=False)

    def code_repl(m: re.Match) -> str:
        return f"<code>{m.group(1)}</code>"

    # Must handle code first so *_ inside backticks stay literal (order of
    # application here only matters for speed; escaped markup won't re-match).
    text = re.sub(r"`([^`]+)`", code_repl, text)

    def link_repl(m: re.Match) -> str:
        label, url, title = m.group(1), m.group(2), m.group(3)
        t = f' title="{html.escape(title, quote=True)}"' if title else ""
        return f'<a href="{html.escape(url, quote=True)}"{t}>{label}</a>'

    # [label](url "title") -- label may itself contain inline markup.
    text = re.sub(r"\[([^\]]+)\]\((\S+?)(?:\s+&quot;([^&]+?)&quot;)?\)", link_repl, text)

    def img_repl(m: re.Match) -> str:
        alt, url, title = m.group(1), m.group(2), m.group(3)
        t = f' title="{html.escape(title, quote=True)}"' if title else ""
        return f'<img src="{html.escape(url, quote=True)}" alt="{alt}"{t}>'

    text = re.sub(r"!\[([^\]]*)\]\((\S+?)(?:\s+&quot;([^&]+?)&quot;)?\)", img_repl, text)

    # Bold / italic. Do bold, then italic, via placeholders to avoid overlap.
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", text)

    return text


def _inline_multi(line: str) -> str:
    return _inline(line)


# --- block rendering --------------------------------------------------------

def _render_code_fence(lines: List[str]) -> Tuple[str, int]:
    """Render a fenced code block starting at lines[0]; return (html, lines consumed)."""
    info = lines[0].strip()[3:].strip()  # language hint after ``` or ~~~
    lang = info.split()[0] if info else ""
    lang_cls = f' class="language-{lang}"' if lang else ""
    buf: List[str] = []
    i = 1
    while i < len(lines) and not lines[i].strip().startswith(lines[0].strip()[0:3]):
        buf.append(lines[i])
        i += 1
    if i < len(lines):
        i += 1  # consume closing fence
    body = html.escape("\n".join(buf))
    return f'<pre><code{lang_cls}>{body}</code></pre>\n', i


def _render_list(lines: List[str], kind: str) -> Tuple[str, int]:
    """Render a list starting at lines[0]; return (html, lines consumed)."""
    tag = "ol" if kind == "ol" else "ul"
    items: List[Tuple[str, List[str]]] = []
    i = 0
    while i < len(lines):
        marker = _is_list_marker(lines[i])
        if not marker:
            break
        _, rest = marker
        item_lines = [rest]
        i += 1
        # Continuation lines: indented non-marker lines belong to this item.
        while i < len(lines):
            if _is_list_marker(lines[i]):
                break
            if lines[i].strip() == "":
                item_lines.append("")
                i += 1
                continue
            m = re.match(r"^\s{2,}(.*)", lines[i])
            if m:
                item_lines.append(m.group(1))
                i += 1
            else:
                break
        # Join with a space, preserving intentional blank candle lines.
        items.append((" ".join(x for x in item_lines if x != ""), item_lines))

    parts: List[str] = [f"<{tag}>"]
    for _, item_lines in items:
        inner = " ".join(x for x in item_lines if x != "")
        parts.append(f"  <li>{_inline_multi(inner)}</li>")
    parts.append(f"</{tag}>")
    return "\n".join(parts) + "\n", i


def _render_table(header_line: str, sep_line: str, rows: List[str]) -> str:
    headers = _parse_table_row(header_line)
    aligns = _parse_table_row(sep_line)
    align_html = []
    for a in aligns:
        if a.startswith(":") and a.endswith(":"):
            align_html.append(' style="text-align:center"')
        elif a.startswith(":"):
            align_html.append(' style="text-align:left"')
        elif a.endswith(":"):
            align_html.append(' style="text-align:right"')
        else:
            align_html.append("")
    out = ["<table>", "<thead><tr>"]
    for h, a in zip(headers, align_html):
        out.append(f"<th{a}>{_inline(h)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        cells = _parse_table_row(row)
        out.append("<tr>")
        for c, a in zip(cells, align_html):
            out.append(f"<td{a}>{_inline(c)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def convert(md: str) -> str:
    """Convert a full markdown document to an HTML string."""
    raw_lines = md.splitlines()
    paras: List[str] = []
    i = 0
    n = len(raw_lines)
    while i < n:
        line = raw_lines[i].rstrip()
        # Fenced code block
        if _is_fence(line):
            block, consumed = _render_code_fence(raw_lines[i:])
            paras.append(block)
            i += consumed
            continue
        # ATX heading
        h = _is_heading(line)
        if h:
            level, text = h
            paras.append(f"<h{level}>{_inline(text)}</h{level}>")
            i += 1
            continue
        # Horizontal rule
        if _is_hr(line):
            paras.append("<hr>")
            i += 1
            continue
        # Blockquote
        if line.lstrip().startswith(">"):
            quoted: List[str] = []
            while i < n and raw_lines[i].lstrip().startswith(">"):
                quoted.append(raw_lines[i].lstrip()[1:].lstrip())
                i += 1
            paras.append(f"<blockquote>\n{convert(chr(10).join(quoted))}\n</blockquote>")
            continue
        # List
        if _is_list_marker(line):
            block, consumed = _render_list(raw_lines[i:], _is_list_marker(line)[0])
            paras.append(block)
            i += consumed
            continue
        # Blank line -> skip, flush pending paragraph
        if line.strip() == "":
            i += 1
            continue
        # Table: header row followed by separator row
        if _is_table_row(line) and i + 1 < n and _is_table_sep(raw_lines[i + 1].strip()):
            header = line
            sep = raw_lines[i + 1].strip()
            rows: List[str] = []
            j = i + 2
            while j < n and _is_table_row(raw_lines[j]):
                rows.append(raw_lines[j])
                j += 1
            paras.append(_render_table(header, sep, rows))
            i = j
            continue
        # Paragraph: gather until blank line or another block start.
        buf = [line.strip()]
        i += 1
        while i < n:
            nx = raw_lines[i].strip()
            if nx == "" or _is_heading(nx) or _is_hr(nx) or _is_fence(nx) \
                    or _is_list_marker(nx) or nx.startswith(">") or _is_table_sep(nx):
                break
            buf.append(nx)
            i += 1
        paras.append(f"<p>{_inline(' '.join(buf))}</p>")

    return "\n\n".join(paras) + "\n"
