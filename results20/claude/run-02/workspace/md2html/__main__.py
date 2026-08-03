"""Command-line interface for md2html.

Reads Markdown from a file (or stdin) and writes HTML to stdout, or to a file
with --output. Basic usage:

    python -m md2html README.md
    echo '# Hi' | python -m md2html
    python -m md2html -o out.html README.md
"""

from __future__ import annotations

import argparse
import sys

from .convert import convert


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="md2html",
        description="Convert Markdown to an HTML fragment (dependency-free).",
    )
    p.add_argument("file", nargs="?", help="input Markdown file (default: stdin)")
    p.add_argument("-o", "--output", help="write HTML to this file (default: stdout)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            source = fh.read()
    else:
        source = sys.stdin.read()

    html = convert(source)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(html)
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
