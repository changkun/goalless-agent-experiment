#!/usr/bin/env python3
"""Print a directory tree with human-readable sizes."""

from __future__ import annotations

import argparse
import os
import sys
from collections import deque
from pathlib import Path


def human_size(size: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ("B", "K", "M", "G", "T", "P"):
        if abs(size) < 1024 or unit == "P":
            if unit == "B":
                return f"{size}{unit}"
            return f"{size / 1024:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}P"  # pragma: no cover


def gather_sizes(root: Path, max_depth: int | None) -> dict[Path, int]:
    """Return cumulative directory sizes and individual file sizes."""
    sizes: dict[Path, int] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)

        # Respect depth limit by pruning dirnames in-place.
        if max_depth is not None:
            depth = len(dir_path.relative_to(root).parts)
            if depth >= max_depth:
                dirnames[:] = []

        file_total = 0
        for name in filenames:
            file_path = dir_path / name
            try:
                file_size = file_path.stat(follow_symlinks=False).st_size
            except (OSError, ValueError):
                file_size = 0
            sizes[file_path] = file_size
            file_total += file_size

        sizes[dir_path] = file_total + sum(
            sizes.get(dir_path / d, 0) for d in dirnames
        )

    return sizes


def tree_lines(
    root: Path,
    sizes: dict[Path, int],
    max_depth: int | None,
    show_files: bool,
) -> list[str]:
    """Generate sorted tree lines."""
    lines: list[str] = []

    def walk(path: Path, prefix: str, depth: int) -> None:
        if max_depth is not None and depth > max_depth:
            return

        try:
            entries = [
                p for p in path.iterdir()
                if not p.is_symlink() and (p.is_dir() or p.is_file())
            ]
        except PermissionError:
            return

        dirs = sorted((p for p in entries if p.is_dir()), key=lambda p: p.name)
        files = sorted((p for p in entries if p.is_file()), key=lambda p: p.name)

        if show_files:
            children = dirs + files
        else:
            children = dirs

        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            connector = "└── " if is_last else "├── "
            size = sizes.get(child, 0)
            suffix = ""
            if child.is_dir():
                children = list(child.iterdir())
                if children:
                    suffix = f"  ({len([c for c in children if c.is_file() or c.is_dir()])} items)"
            lines.append(f"{prefix}{connector}{human_size(size):>6}  {child.name}{suffix}")

            if child.is_dir():
                extension = "    " if is_last else "│   "
                walk(child, prefix + extension, depth + 1)

    lines.append(f"{human_size(sizes.get(root, 0)):>6}  {root.name or str(root)}")
    walk(root, "", 1)
    return lines


def find_largest(root: Path, count: int, max_depth: int | None) -> list[tuple[Path, int]]:
    """Return the largest files under root."""
    sizes = gather_sizes(root, max_depth=None)
    files = [(p, s) for p, s in sizes.items() if p.is_file()]
    files.sort(key=lambda item: item[1], reverse=True)
    return files[:count]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Display directory trees with human-readable sizes."
    )
    parser.add_argument("path", nargs="?", default=".", help="Root directory (default: .)")
    parser.add_argument("-d", "--depth", type=int, help="Maximum depth to display")
    parser.add_argument(
        "--no-files", action="store_true", help="Show only directories"
    )
    parser.add_argument(
        "-l", "--largest", type=int, metavar="N", help="Show top N largest files"
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    if args.largest is not None:
        print(f"Top {args.largest} largest files under {root}:")
        for path, size in find_largest(root, args.largest, args.depth):
            rel = path.relative_to(root)
            print(f"  {human_size(size):>6}  {rel}")
        return 0

    sizes = gather_sizes(root, args.depth)
    for line in tree_lines(root, sizes, args.depth, not args.no_files):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
