#!/usr/bin/env python3
"""tmd — render Markdown to a colorized terminal.

A small, dependency-free Markdown->ANSI renderer built for reading docs
in the terminal. Reads from a file or stdin.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass


# ANSI helpers ---------------------------------------------------------------
@dataclass
class Style:
    bold: str = "\033[1m"
    dim: str = "\033[2m"
    underline: str = "\033[4m"
    reset: str = "\033[0m"
    red: str = "\033[31m"
    green: str = "\033[32m"
    yellow: str = "\033[33m"
    blue: str = "\033[34m"
    magenta: str = "\033[35m"
    cyan: str = "\033[36m"


S = Style()
NO_COLOR = not sys.stdout.isatty() or "-c" in sys.argv or "--no-color" in sys.argv


def paint(text: str, *codes: str) -> str:
    if NO_COLOR:
        return text
    return "".join(codes) + text + S.reset


# Inline parsing -------------------------------------------------------------
CODE_SPAN = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)|(?<!_)_([^_\n]+)_(?!_)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def _escape(text: str) -> str:
    """Escape literal asterisks/underscores so they aren't re-processed."""
    return text.replace("*", "\\*").replace("_", "\\_")


def render_links(text: str) -> str:
    def repl(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        return paint(label, S.underline, S.blue) + paint(f" <{url}>", S.dim)
    return LINK.sub(repl, text)


def render_emphasis(text: str) -> str:
    text = BOLD.sub(lambda m: paint(_escape(m.group(1) or m.group(2)), S.bold), text)
    text = ITALIC.sub(lambda m: paint(_escape(m.group(1) or m.group(2)), S.italic if hasattr(S, "italic") else "\033[3m"), text)
    return text


def render_inline(text: str) -> str:
    text = CODE_SPAN.sub(lambda m: paint(m.group(1), S.green), text)
    text = render_links(text)
    text = render_emphasis(text)
    return text


# Block rendering ------------------------------------------------------------
def render_heading(line: str) -> str:
    match = re.match(r"^(#{1,6})\s+(.*)$", line)
    level = len(match.group(1))
    text = render_inline(match.group(2))
    color = {1: S.bold + S.yellow, 2: S.yellow, 3: S.cyan}.get(level, S.cyan)
    prefix = "#" * level
    return paint(f"{prefix} {text}", color)


def render_list(items: list[str], ordered: bool) -> list[str]:
    out = []
    for i, item in enumerate(items, start=1):
        bullet = f"{i}." if ordered else "•"
        indented = item.replace("\n", "\n" + "   ")
        out.append(paint(f"{bullet} ", S.magenta) + render_inline(indented))
    return out


def render_code_block(lines: list[str]) -> str:
    body = "\n".join(lines)
    return paint(body, S.green) if NO_COLOR else (
        S.dim + "┌────────────────────┐" + S.reset + "\n" +
        "\n".join(paint(l, S.green) for l in lines) + "\n" +
        S.dim + "└────────────────────┘" + S.reset
    )


def render_quote(lines: list[str]) -> str:
    body = "\n".join(lines)
    return paint("│ " + body.replace("\n", "\n│ "), S.dim)


# Document renderer ----------------------------------------------------------
def render_document(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        # Fenced code block
        fence = re.match(r"^```(\w*)\s*$", line)
        if fence:
            lang = fence.group(1)
            block = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            if lang:
                out.append(paint(lang, S.dim))
            out.append(render_code_block(block))
            continue

        # Heading
        if re.match(r"^#{1,6}\s", line):
            out.append(render_heading(line))
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^(\s*([-*_])\s*){3,}$", line) and set(line.strip()) in ({'-'}, {'*'}, {'_'}):
            out.append(paint("─" * 40, S.dim))
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append(render_quote(block))
            continue

        # Lists
        if re.match(r"^(\s*)[-*+]\s+", line) or re.match(r"^(\s*)\d+[.)]\s+", line):
            ordered = bool(re.match(r"^\s*\d+[.)]\s+", line))
            items = []
            while i < n:
                cur = lines[i]
                if re.match(r"^(\s*)[-*+]\s+", cur) or re.match(r"^(\s*)\d+[.)]\s+", cur):
                    item = re.sub(r"^(\s*)[-*+]\s+", "", cur)
                    item = re.sub(r"^(\s*)\d+[.)]\s+", "", item)
                    items.append(item)
                    i += 1
                else:
                    break
            out.extend(render_list(items, ordered))
            continue

        # Paragraph
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^#{1,6}\s", lines[i]) and not lines[i].strip().startswith("```") and not lines[i].lstrip().startswith(">"):
            para.append(lines[i].rstrip())
            i += 1
        out.append(render_inline(" ".join(p.strip() for p in para)))
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def read_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    args = [a for a in args if a not in ("-c", "--no-color")]
    if len(args) > 1:
        print("usage: tmd [file]  (reads stdin if no file)", file=sys.stderr)
        return 2
    try:
        doc = read_input(args[0] if args else None)
    except OSError as exc:
        print(f"tmd: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(render_document(doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
