#!/usr/bin/env python3
"""Create a compact Markdown inventory for a directory tree."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_IGNORES = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".next",
        ".nuxt",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "venv",
    }
)


@dataclass(frozen=True)
class FileInfo:
    path: Path
    size: int


@dataclass(frozen=True)
class Digest:
    root: Path
    files: tuple[FileInfo, ...]
    directories: int
    skipped_dirs: tuple[Path, ...]
    skipped_files: tuple[Path, ...]

    @property
    def total_size(self) -> int:
        return sum(file.size for file in self.files)

    @property
    def extension_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for file in self.files:
            counts[_extension_label(file.path)] += 1
        return counts

    @property
    def extension_sizes(self) -> Counter[str]:
        sizes: Counter[str] = Counter()
        for file in self.files:
            sizes[_extension_label(file.path)] += file.size
        return sizes


def scan_tree(root: Path, ignored_names: Iterable[str] = DEFAULT_IGNORES) -> Digest:
    """Scan root and return file metadata, skipping directories by basename."""

    root = root.expanduser().resolve()
    ignored = set(ignored_names)

    if not root.exists():
        raise FileNotFoundError(root)

    if root.is_file():
        try:
            return Digest(root.parent, (FileInfo(root.name, root.stat().st_size),), 0, (), ())
        except OSError:
            return Digest(root.parent, (), 0, (), (Path(root.name),))

    files: list[FileInfo] = []
    skipped_dirs: list[Path] = []
    skipped_files: list[Path] = []
    directory_count = 0

    for current, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current)

        kept_dirs: list[str] = []
        for dirname in sorted(dirnames):
            directory_path = current_path / dirname
            relative_dir = directory_path.relative_to(root)
            if dirname in ignored:
                skipped_dirs.append(relative_dir)
            else:
                kept_dirs.append(dirname)

        dirnames[:] = kept_dirs
        directory_count += len(kept_dirs)

        for filename in sorted(filenames):
            path = current_path / filename
            try:
                stat = path.stat()
            except OSError:
                skipped_files.append(path.relative_to(root))
                continue

            if not path.is_file():
                continue

            files.append(FileInfo(path.relative_to(root), stat.st_size))

    return Digest(
        root=root,
        files=tuple(sorted(files, key=lambda file: str(file.path))),
        directories=directory_count,
        skipped_dirs=tuple(sorted(skipped_dirs, key=str)),
        skipped_files=tuple(sorted(skipped_files, key=str)),
    )


def render_markdown(digest: Digest, top: int = 10, file_limit: int = 80) -> str:
    top = max(1, top)
    file_limit = max(1, file_limit)

    lines = [
        f"# Workspace Digest: `{digest.root}`",
        "",
        "## Summary",
        "",
        f"- Files: {len(digest.files)}",
        f"- Directories: {digest.directories}",
        f"- Total size: {_format_size(digest.total_size)}",
    ]

    if digest.skipped_dirs:
        lines.append(f"- Skipped directories: {len(digest.skipped_dirs)}")
    if digest.skipped_files:
        lines.append(f"- Skipped files: {len(digest.skipped_files)}")

    lines.extend(["", "## File Types", "", "| Type | Files | Size |", "| --- | ---: | ---: |"])
    extension_sizes = digest.extension_sizes
    extension_rows = sorted(
        digest.extension_counts.items(),
        key=lambda item: (-extension_sizes[item[0]], item[0]),
    )
    if extension_rows:
        for extension, count in extension_rows:
            lines.append(f"| `{extension}` | {count} | {_format_size(extension_sizes[extension])} |")
    else:
        lines.append("| `(none)` | 0 | 0 B |")

    lines.extend(["", f"## Largest Files", "", "| Path | Size |", "| --- | ---: |"])
    largest = sorted(digest.files, key=lambda file: (-file.size, str(file.path)))[:top]
    if largest:
        for file in largest:
            lines.append(f"| `{file.path.as_posix()}` | {_format_size(file.size)} |")
    else:
        lines.append("| `(none)` | 0 B |")

    lines.extend(["", f"## Files ({min(len(digest.files), file_limit)} of {len(digest.files)})", "", "```"])
    for file in digest.files[:file_limit]:
        lines.append(file.path.as_posix())
    if len(digest.files) > file_limit:
        lines.append(f"... {len(digest.files) - file_limit} more")
    lines.append("```")

    if digest.skipped_dirs:
        lines.extend(["", "## Skipped Directories", "", "```"])
        for path in digest.skipped_dirs[:file_limit]:
            lines.append(path.as_posix())
        if len(digest.skipped_dirs) > file_limit:
            lines.append(f"... {len(digest.skipped_dirs) - file_limit} more")
        lines.append("```")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a compact Markdown inventory for a directory tree."
    )
    parser.add_argument("root", nargs="?", default=".", type=Path, help="Directory or file to scan.")
    parser.add_argument("--top", type=int, default=10, help="Number of largest files to show.")
    parser.add_argument(
        "--file-limit",
        type=int,
        default=80,
        help="Maximum number of file paths to list.",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="NAME",
        help="Additional directory basename to skip. Can be passed multiple times.",
    )
    parser.add_argument(
        "--no-default-ignores",
        action="store_true",
        help="Only use names passed with --ignore.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write Markdown to a file instead of stdout.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ignored_names = set(args.ignore)
    if not args.no_default_ignores:
        ignored_names.update(DEFAULT_IGNORES)

    try:
        digest = scan_tree(args.root, ignored_names)
    except FileNotFoundError as exc:
        parser.error(f"path does not exist: {exc.filename}")

    output = render_markdown(digest, top=args.top, file_limit=args.file_limit)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    return 0


def _extension_label(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else "[none]"


def _format_size(size: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(size)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(amount)} {unit}"
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{size} B"


if __name__ == "__main__":
    raise SystemExit(main())
