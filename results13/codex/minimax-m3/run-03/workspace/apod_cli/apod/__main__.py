"""Command-line interface for apod_cli."""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from .client import ApodError, ApodData, fetch_apod, fetch_range
from .render import render_html, render_markdown, render_terminal


_FORMATS = {"term", "md", "html"}


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r} (expected YYYY-MM-DD)"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="apod",
        description="Show NASA's Astronomy Picture of the Day in your terminal.",
    )
    p.add_argument("date", nargs="?", type=_parse_date, help="Date (YYYY-MM-DD); defaults to today.")
    p.add_argument("--random", action="store_true", help="Fetch a random APOD entry.")
    p.add_argument(
        "--range",
        nargs=2,
        metavar=("START", "END"),
        type=_parse_date,
        help="Fetch a range of dates (inclusive).",
    )
    p.add_argument(
        "--format",
        choices=sorted(_FORMATS),
        default="term",
        help="Output format: term (default), md, html.",
    )
    p.add_argument(
        "-o", "--output",
        type=Path,
        help="Write to this file instead of stdout (useful for md/html).",
    )
    p.add_argument(
        "--width", type=int, default=88,
        help="Terminal render width (default: 88).",
    )
    p.add_argument(
        "--title", default="NASA APOD",
        help="Document title for HTML output (default: NASA APOD).",
    )
    p.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI colors in terminal output.",
    )
    return p


def _resolve_items(args: argparse.Namespace) -> list[ApodData]:
    if args.range:
        start, end = args.range
        return fetch_range(start, end)
    return [fetch_apod(args.date, random_pick=args.random)]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.no_color:
        import apod.render as r
        r._COLOR = False  # type: ignore[attr-defined]

    try:
        items = _resolve_items(args)
    except ApodError as exc:
        print(f"apod: {exc}", file=sys.stderr)
        return 2

    if args.format == "term":
        out = render_terminal(items, width=args.width)
    elif args.format == "md":
        out = render_markdown(items)
    elif args.format == "html":
        out = render_html(items, title=args.title)
    else:  # pragma: no cover — argparse enforces choices
        parser.error(f"unknown format: {args.format}")
        return 2

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
