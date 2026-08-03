#!/usr/bin/env python3
"""mdterm - render Markdown to a styled terminal, using only the stdlib.

Renders headings, emphasis, code, links, lists, blockquotes, fenced code,
and horizontal rules with ANSI colors. Purely for fun and terminal display.
"""

import argparse
import re
import sys

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
UNDERLINE = "\x1b[4m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
CYAN = "\x1b[36m"
MAGENTA = "\x1b[35m"
GREY = "\x1b[90m"

NO_COLOR = 0
MIN_COLOR = 1
FULL_COLOR = 2

CODE_SPAN = re.compile(r"`([^`]+)`")
EMPH = re.compile(r"(\*\*|__)(.+?)\1|(\*|_)([^*_]+)\3")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?: \"([^\"]+)\")?\)")
AUTO_LINK = re.compile(r"<((?:https?|mailto):[^>]+)>")


def render_inline(text, level=NO_COLOR):
    """Apply inline markdown: links, code, and emphasis."""
    if level == NO_COLOR:
        text = re.sub(r"\[([^\]]+)\]\([^)\s]+(?: \"[^\"]*\")?\)", r"\1", text)
        text = CODE_SPAN.sub(r"\1", text)
        text = re.sub(r"(\*\*|__|\*|_)([^*_]+)\1", r"\2", text)
        return text

    def link_repl(m):
        label, url = m.group(1), m.group(2)
        return f"{UNDERLINE}{CYAN}{render_inline(label, level)}{RESET} ({DIM}{url}{RESET})"

    def code_repl(m):
        return f"{RED}{m.group(1)}{RESET}"

    def emph_repl(m):
        if m.group(1):
            return f"{BOLD}{render_inline(m.group(2), level)}{RESET}"
        return f"{MAGENTA}{m.group(4)}{RESET}"

    text = LINK.sub(link_repl, text)
    text = AUTO_LINK.sub(lambda m: f"{CYAN}{UNDERLINE}{m.group(1)}{RESET}", text)
    text = CODE_SPAN.sub(code_repl, text)
    text = EMPH.sub(emph_repl, text)
    return text


def _style(style, text):
    return f"{style}{text}{RESET}"


def _headline(title, style):
    return _style(style, title) + f" {DIM}{'─' * max(0, 60 - len(title))}{RESET}"


def render(source, level=FULL_COLOR):
    colored = level != NO_COLOR

    def style(style, text, plain=""):
        return _style(style, text) if colored else (plain if plain else text)

    lines = source.splitlines()
    out = []
    i = 0
    in_code = False

    while i < len(lines):
        line = lines[i]

        fence = re.match(r"^\s*(```|~~~)(\S*)\s*$", line)
        if fence:
            if not in_code:
                in_code = True
                lang = fence.group(2)
                if colored:
                    out.append(f"{DIM}┌─ {lang or 'code'}{RESET}")
            else:
                in_code = False
                if colored:
                    out.append(f"{DIM}└─{RESET}")
            i += 1
            continue

        if in_code:
            out.append(line)
            i += 1
            continue

        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            lvl = len(hm.group(1))
            heading_style = [BOLD, GREEN, YELLOW, CYAN, MAGENTA, DIM][min(lvl, 6) - 1]
            title = render_inline(hm.group(2), level)
            if colored:
                out.append(_headline(title, heading_style))
            else:
                out.append(title)
            i += 1
            continue

        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append(_style(GREY, "─" * 60) if colored else "─" * 60)
            i += 1
            continue

        if re.match(r"^\s*>\s?", line):
            quote = re.sub(r"^\s*>\s?", "", line)
            rendered = render_inline(quote, level)
            out.append(style(GREY, f"│ {rendered}", f"> {quote}"))
            i += 1
            continue

        lm = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)$", line)
        if lm:
            marker, content = lm.group(1), lm.group(2)
            rendered = render_inline(content, level)
            out.append(f"  {style(GREEN, marker, marker)} {rendered}")
            i += 1
            continue

        if not line.strip():
            out.append("")
            i += 1
            continue

        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,6}\s|```|~~~|\s*>|$)", lines[i]
        ):
            para.append(lines[i])
            i += 1
        out.append(render_inline(" ".join(p.strip() for p in para), level))

    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render Markdown to the terminal.")
    parser.add_argument("file", nargs="?", help="Markdown file to render (defaults to stdin)")
    parser.add_argument(
        "--color",
        choices=["full", "min", "none"],
        default="full",
        help="Color level (default: full)",
    )
    args = parser.parse_args(argv)

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            src = fh.read()
    else:
        src = sys.stdin.read()

    level = {"full": FULL_COLOR, "min": MIN_COLOR, "none": NO_COLOR}[args.color]
    print(render(src, level))


if __name__ == "__main__":
    main()
