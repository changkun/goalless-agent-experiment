"""Command-line entry point for mdgen."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import ParseError, render_html, render_markdown


def build_site(src: Path, out: Path) -> list[Path]:
    """Build every .md file from src into a sibling .html file under out."""
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for md in sorted(src.rglob("*.md")):
        rel = md.relative_to(src)
        target = (out / rel).with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        text = md.read_text(encoding="utf-8")
        title = md.stem.replace("_", " ").replace("-", " ").title()
        target.write_text(render_html(text, title), encoding="utf-8")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdgen",
        description="Build a static HTML site from Markdown files.",
    )
    parser.add_argument("input", nargs="?", default=".", help="input directory or a .md file")
    parser.add_argument("output", nargs="?", default="site", help="output directory")
    parser.add_argument("--title", default="Untitled", help="page title (single-file mode)")
    parser.add_argument("--stdout", action="store_true", help="print HTML to stdout (single-file mode)")
    args = parser.parse_args(argv)

    inp = Path(args.input)

    try:
        if args.stdout or inp.is_file():
            text = inp.read_text(encoding="utf-8") if inp.is_file() else sys.stdin.read()
            result = render_html(text, args.title)
            sys.stdout.write(result)
            return 0
        written = build_site(inp, Path(args.output))
    except (ParseError, OSError, UnicodeDecodeError) as exc:
        print(f"mdgen: error: {exc}", file=sys.stderr)
        return 1

    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
