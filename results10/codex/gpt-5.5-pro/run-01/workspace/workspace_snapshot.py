#!/usr/bin/env python3
"""Summarize a source workspace from the command line."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_IGNORES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}

LANGUAGES_BY_SUFFIX = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".lua": "Lua",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".txt": "Text",
    ".yaml": "YAML",
    ".yml": "YAML",
}

TODO_RE = re.compile(
    r"(?:^|\s)(#|//|--|/\*+|\*|<!--)\s*(TODO|FIXME|HACK|XXX)\b[:\s-]*(.*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FileInfo:
    path: str
    bytes: int
    language: str


@dataclass(frozen=True)
class LanguageSummary:
    language: str
    files: int
    bytes: int


@dataclass(frozen=True)
class Todo:
    path: str
    line: int
    tag: str
    text: str


@dataclass(frozen=True)
class Snapshot:
    root: str
    files: int
    bytes: int
    languages: list[LanguageSummary]
    largest_files: list[FileInfo]
    todos: list[Todo]
    skipped: list[str]


def language_for(path: Path) -> str:
    """Return a broad language label for a file path."""
    if path.name in {"Dockerfile", "Makefile"}:
        return path.name
    return LANGUAGES_BY_SUFFIX.get(path.suffix.lower(), "Other")


def should_ignore(path: Path, ignore_names: set[str], include_hidden: bool) -> bool:
    if path.name in ignore_names:
        return True
    return not include_hidden and path.name.startswith(".")


def iter_files(root: Path, ignore_names: set[str], include_hidden: bool) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [
            name
            for name in dirs
            if not should_ignore(current_path / name, ignore_names, include_hidden)
        ]
        for name in files:
            file_path = current_path / name
            if not should_ignore(file_path, ignore_names, include_hidden):
                yield file_path


def read_text_lines(path: Path, max_bytes: int = 1_000_000) -> list[str] | None:
    try:
        with path.open("rb") as handle:
            data = handle.read(max_bytes)
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace").splitlines()


def find_todos(path: Path, root: Path, limit: int) -> list[Todo]:
    lines = read_text_lines(path)
    if lines is None:
        return []

    todos: list[Todo] = []
    relative = str(path.relative_to(root))
    for line_no, line in enumerate(lines, start=1):
        match = TODO_RE.search(line)
        if match:
            text = match.group(3).strip()
            for suffix in ("*/", "-->"):
                if text.endswith(suffix):
                    text = text[: -len(suffix)].rstrip()
            todos.append(
                Todo(
                    path=relative,
                    line=line_no,
                    tag=match.group(2).upper(),
                    text=text,
                )
            )
        if len(todos) >= limit:
            break
    return todos


def build_snapshot(
    root: Path,
    *,
    max_files: int,
    max_todos: int,
    ignore_names: set[str] | None = None,
    include_hidden: bool = False,
) -> Snapshot:
    root = root.resolve()
    ignore_names = set(DEFAULT_IGNORES if ignore_names is None else ignore_names)

    files: list[FileInfo] = []
    skipped: list[str] = []
    todos: list[Todo] = []
    language_totals: dict[str, tuple[int, int]] = {}

    for path in iter_files(root, ignore_names, include_hidden):
        try:
            stat = path.stat()
        except OSError as exc:
            skipped.append(f"{path.relative_to(root)}: {exc}")
            continue

        language = language_for(path)
        relative = str(path.relative_to(root))
        files.append(FileInfo(path=relative, bytes=stat.st_size, language=language))

        count, byte_count = language_totals.get(language, (0, 0))
        language_totals[language] = (count + 1, byte_count + stat.st_size)

        remaining_todos = max_todos - len(todos)
        if remaining_todos > 0:
            todos.extend(find_todos(path, root, remaining_todos))

    languages = [
        LanguageSummary(language=language, files=count, bytes=byte_count)
        for language, (count, byte_count) in language_totals.items()
    ]
    languages.sort(key=lambda item: (-item.bytes, item.language))

    largest_files = sorted(files, key=lambda item: item.bytes, reverse=True)[:max_files]

    return Snapshot(
        root=str(root),
        files=len(files),
        bytes=sum(item.bytes for item in files),
        languages=languages,
        largest_files=largest_files,
        todos=todos,
        skipped=skipped,
    )


def format_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{value} B"
        size /= 1024
    return f"{value} B"


def print_human(snapshot: Snapshot) -> None:
    print(f"Workspace: {snapshot.root}")
    print(f"Files: {snapshot.files}")
    print(f"Size: {format_bytes(snapshot.bytes)}")

    print("\nLanguages:")
    if snapshot.languages:
        for item in snapshot.languages:
            print(f"  {item.language}: {item.files} files, {format_bytes(item.bytes)}")
    else:
        print("  None")

    print("\nLargest files:")
    if snapshot.largest_files:
        for item in snapshot.largest_files:
            print(f"  {format_bytes(item.bytes):>10}  {item.path}")
    else:
        print("  None")

    print("\nTODOs:")
    if snapshot.todos:
        for item in snapshot.todos:
            text = f" {item.text}" if item.text else ""
            print(f"  {item.path}:{item.line}  {item.tag}{text}")
    else:
        print("  None")

    if snapshot.skipped:
        print("\nSkipped:")
        for item in snapshot.skipped:
            print(f"  {item}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize files, languages, large files, and TODO comments in a workspace."
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to scan.")
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories, except explicit ignores.",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="NAME",
        help="Directory or file name to ignore. May be repeated.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Number of largest files to show.",
    )
    parser.add_argument(
        "--max-todos",
        type=int,
        default=20,
        help="Maximum TODO-like comments to report.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.path)
    if not root.exists():
        print(f"error: path does not exist: {root}", file=os.sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: path is not a directory: {root}", file=os.sys.stderr)
        return 2
    if args.max_files < 0 or args.max_todos < 0:
        print("error: --max-files and --max-todos must be non-negative", file=os.sys.stderr)
        return 2

    ignore_names = DEFAULT_IGNORES | set(args.ignore)
    snapshot = build_snapshot(
        root,
        max_files=args.max_files,
        max_todos=args.max_todos,
        ignore_names=ignore_names,
        include_hidden=args.include_hidden,
    )

    if args.json:
        print(json.dumps(asdict(snapshot), indent=2))
    else:
        print_human(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
