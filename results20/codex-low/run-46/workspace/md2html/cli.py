"""Command-line interface for md2html."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from md2html.converter import convert


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="md2html",
        description="Convert a Markdown file (or stdin) to an HTML fragment.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown file to read; reads stdin if omitted.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Write HTML to this file instead of stdout.",
    )
    args = parser.parse_args(argv)

    try:
        source = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
        result = convert(source)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"md2html: error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        try:
            Path(args.output).write_text(result, encoding="utf-8")
        except OSError as exc:
            print(f"md2html: error: {exc}", file=sys.stderr)
            return 1
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
