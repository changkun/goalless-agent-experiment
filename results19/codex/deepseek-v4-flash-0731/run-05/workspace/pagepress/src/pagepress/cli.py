"""Command-line interface for pagepress."""

import argparse
import sys
from pathlib import Path

from .md import markdown, extract_title

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def render(md_text: str, default_title: str = "Untitled") -> str:
    title = extract_title(md_text) or default_title
    return TEMPLATE.format(title=title, body=markdown(md_text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pagepress",
        description="Convert Markdown to a standalone styled HTML page.",
    )
    parser.add_argument("input", nargs="?", help="Markdown input file (reads stdin if omitted)")
    parser.add_argument("-o", "--output", help="Output HTML file (prints to stdout if omitted)")
    parser.add_argument("-t", "--title", default="Untitled", help="Fallback page title")
    args = parser.parse_args(argv)

    if args.input:
        try:
            md_text = Path(args.input).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"pagepress: cannot read {args.input}: {exc}", file=sys.stderr)
            return 1
    else:
        md_text = sys.stdin.read()

    html = render(md_text, args.title)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
    else:
        print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
