"""Command line interface for mdgen."""
from __future__ import annotations

import argparse
import pathlib
import sys

from .parser import to_html

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def _title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def render_page(markdown: str, title: str | None = None) -> str:
    """Wrap rendered markdown in a minimal HTML document."""
    body = to_html(markdown)
    resolved = title or _title(markdown, "mdgen page")
    return TEMPLATE.format(title=resolved, body=body)


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(input_dir: pathlib.Path, output_dir: pathlib.Path) -> None:
    """Recursively convert every .md file under input_dir into .html."""
    for source in sorted(input_dir.rglob("*.md")):
        relative = source.relative_to(input_dir).with_suffix(".html")
        target = output_dir / relative
        markdown = source.read_text(encoding="utf-8")
        _write(target, render_page(markdown))
        print(f"built {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdgen",
        description="Convert Markdown files into standalone HTML pages.",
    )
    parser.add_argument("input", type=pathlib.Path, help="input file or directory")
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        help="output directory (directory builds) or output file (single files)",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="page title, overrides the first level-1 heading",
    )
    args = parser.parse_args(argv)

    if args.input.is_dir():
        output = args.output or args.input.parent / "dist"
        build(args.input, output)
    else:
        markdown = args.input.read_text(encoding="utf-8")
        print(render_page(markdown, args.title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
