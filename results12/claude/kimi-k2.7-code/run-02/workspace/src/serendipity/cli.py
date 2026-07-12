"""Command-line interface for serendipity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from serendipity.data import Category, load_prompts, pick


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="serendipity",
        description="A tiny CLI for random curiosity prompts and micro-adventures.",
    )
    parser.add_argument(
        "-c",
        "--category",
        choices=[c.name.lower() for c in Category],
        help="Filter prompts by category",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to a JSON file of custom prompts",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all available prompts",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def render_prompt(prompt) -> Panel:
    """Render a single prompt as a rich Panel."""
    body = Text.assemble(
        (prompt.text, "bold cyan"),
        "\n\n",
        ("Why? ", "italic dim"),
        (prompt.why, "italic"),
    )
    return Panel(
        body,
        title=f"[{prompt.category}]",
        title_align="left",
        border_style="green",
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    category = Category[args.category.upper()] if args.category else None
    prompts = load_prompts(args.file)

    if args.list:
        for prompt in prompts:
            if category is None or prompt.category == category:
                console.print(render_prompt(prompt))
        return 0

    prompt = pick(prompts, category)
    if prompt is None:
        console.print("[red]No prompts found.[/red]")
        return 1

    console.print(render_prompt(prompt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
