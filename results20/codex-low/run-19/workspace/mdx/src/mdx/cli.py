"""Command-line interface for mdx."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import convert, render_html


def _discover(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def build(src: Path, out: Path) -> None:
    for md in _discover(src):
        rel = md.relative_to(src)
        html_path = out / rel.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        text = md.read_text(encoding="utf-8")
        body = convert(text)
        doc = render_html(md.stem, body)
        html_path.write_text(doc, encoding="utf-8")
        print(f"{md} -> {html_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdx",
        description="Convert Markdown to HTML fragments or full documents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("convert", help="convert markdown files to HTML")
    one.add_argument("files", nargs="+", type=Path, help="markdown input files")
    one.add_argument("-o", "--output", type=Path, help="write output to a file")
    one.add_argument("--full", action="store_true", help="emit a full HTML document")
    one.add_argument("-t", "--title", default="Document", help="title for --full output")

    site = sub.add_parser("build", help="build a whole site from a directory")
    site.add_argument("src", type=Path, help="source directory of .md files")
    site.add_argument("out", type=Path, help="output directory")

    args = parser.parse_args(argv)

    if args.command == "convert":
        for path in args.files:
            text = path.read_text(encoding="utf-8")
            body = convert(text)
            result = render_html(args.title, body) if args.full else body
            if args.output:
                args.output.write_text(result, encoding="utf-8")
            else:
                sys.stdout.write(result + ("\n" if not args.full else ""))
        return 0

    if args.command == "build":
        build(args.src, args.out)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
