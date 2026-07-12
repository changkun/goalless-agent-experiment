"""Renderers for ApodData: terminal (ANSI), Markdown, and HTML."""
from __future__ import annotations

import html
import os
import re
import shutil
import sys
import textwrap
from typing import Iterable, Sequence

from .client import ApodData

# --- ANSI helpers ------------------------------------------------------------

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_DIM = "\x1b[2m"
_ITALIC = "\x1b[3m"
_UNDERLINE = "\x1b[4m"

_CYAN = "\x1b[36m"
_MAGENTA = "\x1b[35m"
_YELLOW = "\x1b[33m"
_BLUE = "\x1b[34m"
_GREEN = "\x1b[32m"
_GREY = "\x1b[90m"


def _supports_color() -> bool:
    try:
        isatty = sys.stdout.isatty()
    except (AttributeError, ValueError):
        isatty = False
    if not isatty:
        return False
    term = os.environ.get("TERM", "")
    if not term or term == "dumb":
        return False
    return "color" in term or "xterm" in term or "screen" in term or term.endswith("-256color")


_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    return f"{code}{text}{_RESET}" if _COLOR else text


def _hr(width: int, char: str = "─") -> str:
    return _c(_GREY, char * max(8, width))


def _wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(paragraph, width=width, replace_whitespace=False, drop_whitespace=False) or [""])
    return out


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


# --- terminal ----------------------------------------------------------------

def render_terminal(items: Sequence[ApodData], width: int = 88) -> str:
    if not items:
        return _c(_DIM, "No APOD entries to display.")
    width = max(40, min(shutil.get_terminal_size((width, 20)).columns, width))
    chunks: list[str] = []
    for i, item in enumerate(items):
        chunks.append(_render_one(item, width))
        if i != len(items) - 1:
            chunks.append("")
    return "\n".join(chunks)


def _render_one(item: ApodData, width: int) -> str:
    title = _c(_BOLD + _MAGENTA, f"✦  {item.title}")
    date_str = _c(_CYAN, item.date.strftime("%A, %B %d, %Y"))
    media = _c(_YELLOW, f"[{item.media_type.upper()}]")
    header = f"{title}  {date_str}  {media}"

    explanation = _strip_html(item.explanation)
    body_lines: list[str] = []
    for line in _wrap(explanation, width - 4):
        body_lines.append("  " + line)

    meta: list[str] = []
    meta.append("  " + _c(_DIM, "URL:  ") + _c(_UNDERLINE + _BLUE, item.url))
    if item.hdurl and item.hdurl != item.url:
        meta.append("  " + _c(_DIM, "HD:   ") + _c(_UNDERLINE + _BLUE, item.hdurl))
    if item.copyright:
        credit = item.copyright
        if not credit.lower().startswith("copyright") and not credit.lower().startswith("©"):
            credit = f"© {credit}"
        meta.append("  " + _c(_DIM, "By:   ") + _c(_ITALIC + _GREEN, credit))
    if item.service_version:
        meta.append("  " + _c(_DIM, "API:  ") + _c(_GREY, f"{item.service_version}"))

    return "\n".join([header, _hr(width), *body_lines, _hr(width), *meta])


# --- markdown ----------------------------------------------------------------

def render_markdown(items: Iterable[ApodData]) -> str:
    out: list[str] = []
    for item in items:
        out.append(f"# ✦ {item.title}")
        out.append("")
        out.append(f"**{item.date.strftime('%A, %B %d, %Y')}** — `{item.media_type}`")
        out.append("")
        if item.is_image:
            out.append(f"![{item.title}]({item.hdurl or item.url})")
            out.append("")
        out.append(_strip_html(item.explanation))
        out.append("")
        if item.copyright:
            out.append(f"*{item.copyright}*")
            out.append("")
        out.append(f"[Open on NASA]({item.url})")
        if item.hdurl and item.hdurl != item.url:
            out.append(f" • [HD version]({item.hdurl})")
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --- html --------------------------------------------------------------------

_HTML_CSS = """
:root { color-scheme: dark light; }
body { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
       max-width: 760px; margin: 2.5rem auto; padding: 0 1.25rem; line-height: 1.6;
       color: #e7e9ee; background: #0b0d12; }
h1 { font-size: 1.9rem; margin: 0 0 .25rem; color: #f0c674; }
.meta { color: #8ab4f8; font-size: .95rem; margin-bottom: 1.25rem; }
img { max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,.45); }
p { white-space: pre-wrap; }
.credit { color: #7fd1ae; font-style: italic; margin-top: 1rem; }
.links a { color: #8ab4f8; margin-right: .75rem; }
hr { border: none; border-top: 1px solid #2a2f3a; margin: 2.5rem 0; }
"""


def render_html(items: Iterable[ApodData], *, title: str = "NASA APOD") -> str:
    body: list[str] = []
    for item in items:
        media = html.escape(item.media_type)
        img = ""
        if item.is_image:
            src = html.escape(item.hdurl or item.url, quote=True)
            alt = html.escape(item.title, quote=True)
            img = f'<img src="{src}" alt="{alt}">'
        body.append(f"<h1>✦ {html.escape(item.title)}</h1>")
        body.append(f'<div class="meta">{html.escape(item.date.strftime("%A, %B %d, %Y"))} — <code>{media}</code></div>')
        if img:
            body.append(img)
        for para in item.explanation.split("\n\n"):
            body.append(f"<p>{html.escape(para)}</p>")
        if item.copyright:
            body.append(f'<p class="credit">{html.escape(item.copyright)}</p>')
        links = [f'<a href="{html.escape(item.url, quote=True)}">Open on NASA</a>']
        if item.hdurl and item.hdurl != item.url:
            links.append(f'<a href="{html.escape(item.hdurl, quote=True)}">HD version</a>')
        body.append(f'<p class="links">{" ".join(links)}</p>')
        body.append("<hr>")

    return (
        "<!doctype html>\n"
        f"<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{html.escape(title)}</title><style>{_HTML_CSS}</style></head>"
        f"<body>{''.join(body)}</body></html>\n"
    )
