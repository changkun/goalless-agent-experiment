#!/usr/bin/env python3
"""Tiny standup-note tracker."""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_NOTES_DIR = Path.home() / ".standup"


def notes_dir(path: Path | None = None) -> Path:
    p = path or DEFAULT_NOTES_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def today_file(root: Path) -> Path:
    return root / f"{date.today().isoformat()}.md"


def cmd_log(args: argparse.Namespace) -> int:
    root = notes_dir(args.dir)
    note = today_file(root)
    if args.message:
        text = " ".join(args.message)
    else:
        prompt = "What did you work on today? (Ctrl-D to finish)\n"
        if sys.stdin.isatty():
            sys.stdout.write(prompt)
            sys.stdout.flush()
        text = sys.stdin.read().strip()

    if not text:
        sys.stderr.write("error: empty note, nothing saved.\n")
        return 1

    with note.open("a", encoding="utf-8") as f:
        f.write(f"- {text}\n")
    print(f"Logged to {note}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = notes_dir(args.dir)
    files = sorted(root.glob("*.md"), reverse=True)
    limit = args.n if args.n else len(files)
    for note in files[:limit]:
        print(note.name)
        if args.show:
            print(note.read_text(encoding="utf-8").rstrip())
            print()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = notes_dir(args.dir)
    pattern = re.compile(args.pattern, re.IGNORECASE)
    for note in sorted(root.glob("*.md"), reverse=True):
        hits = [line for line in note.read_text(encoding="utf-8").splitlines() if pattern.search(line)]
        if hits:
            print(note.name)
            for line in hits:
                print(f"  {line}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track daily standup notes.")
    parser.add_argument("--dir", type=Path, help="notes directory")
    sub = parser.add_subparsers(dest="command", required=True)

    log = sub.add_parser("log", help="add a note for today")
    log.add_argument("message", nargs="*", help="note text")

    lst = sub.add_parser("list", help="list recent notes")
    lst.add_argument("-n", type=int, help="limit number of days")
    lst.add_argument("--show", action="store_true", help="print contents")

    search = sub.add_parser("search", help="search notes by regex")
    search.add_argument("pattern", help="regex pattern")

    args = parser.parse_args(argv)
    match args.command:
        case "log":
            return cmd_log(args)
        case "list":
            return cmd_list(args)
        case "search":
            return cmd_search(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
