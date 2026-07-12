#!/usr/bin/env python3
"""
organize.py - Sort files in a directory into subfolders by extension.

Usage:
    python organize.py [DIRECTORY] [--dry-run]

Example:
    python organize.py ~/Downloads
    python organize.py . --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize files into subdirectories by extension."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to organize (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without moving files.",
    )
    return parser.parse_args(argv)


def organize(directory: Path, dry_run: bool = False) -> dict[str, int]:
    """Move loose files in *directory* into extension-named subfolders.

    Returns a mapping of extension -> number of files moved.
    """
    if not directory.is_dir():
        raise SystemExit(f"Error: {directory} is not a directory.")

    counts: dict[str, int] = {}

    for path in directory.iterdir():
        if not path.is_file():
            continue
        if path.name == "organize.py":
            # Avoid moving the script itself when run from its own directory.
            continue

        ext = path.suffix.lstrip(".").lower() or "no_extension"
        dest_dir = directory / ext
        dest = dest_dir / path.name

        counts[ext] = counts.get(ext, 0) + 1

        if dry_run:
            print(f"Would move: {path.name} -> {dest}")
            continue

        dest_dir.mkdir(exist_ok=True)

        # Handle name collisions by appending a counter.
        counter = 1
        stem = dest.stem
        suffix = dest.suffix
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(path), str(dest))
        print(f"Moved: {path.name} -> {dest}")

    return counts


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.directory).resolve()
    counts = organize(target, dry_run=args.dry_run)

    if not counts:
        print("No files to organize.")
        return 0

    print("\nSummary:")
    for ext, count in sorted(counts.items()):
        print(f"  {ext}: {count} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
