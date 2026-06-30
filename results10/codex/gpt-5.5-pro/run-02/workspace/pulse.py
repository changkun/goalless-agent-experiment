#!/usr/bin/env python3
"""A tiny local decision and note log."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_LOG = Path("pulse.jsonl")


@dataclass(frozen=True)
class Entry:
    entry_id: int
    text: str
    created_at: str
    tags: tuple[str, ...]
    why: str | None = None

    def to_json(self) -> str:
        payload = {
            "id": self.entry_id,
            "text": self.text,
            "created_at": self.created_at,
            "tags": list(self.tags),
        }
        if self.why:
            payload["why"] = self.why
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Entry":
        try:
            entry_id = payload["id"]
            text = payload["text"]
            created_at = payload["created_at"]
            tags = payload.get("tags", [])
            why = payload.get("why")
        except KeyError as exc:
            raise ValueError(f"missing field: {exc.args[0]}") from exc

        if not isinstance(entry_id, int):
            raise ValueError("id must be an integer")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        if not isinstance(created_at, str):
            raise ValueError("created_at must be a string")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("tags must be a list of strings")
        if why is not None and not isinstance(why, str):
            raise ValueError("why must be a string")

        return cls(
            entry_id=entry_id,
            text=text,
            created_at=created_at,
            tags=tuple(tag for tag in tags if tag),
            why=why or None,
        )


def read_entries(path: Path) -> list[Entry]:
    if not path.exists():
        return []

    entries: list[Entry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError("entry must be a JSON object")
                entries.append(Entry.from_dict(payload))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid entry: {exc}") from exc
    return entries


def next_id(entries: Iterable[Entry]) -> int:
    return max((entry.entry_id for entry in entries), default=0) + 1


def normalize_tags(tags: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw_tag in tags:
        tag = raw_tag.strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return tuple(normalized)


def add_entry(path: Path, text: str, tags: Sequence[str], why: str | None) -> Entry:
    entries = read_entries(path)
    entry = Entry(
        entry_id=next_id(entries),
        text=text.strip(),
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        tags=normalize_tags(tags),
        why=why.strip() if why and why.strip() else None,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry.to_json() + "\n")
    return entry


def find_entry(entries: Iterable[Entry], entry_id: int) -> Entry | None:
    return next((entry for entry in entries if entry.entry_id == entry_id), None)


def format_entry(entry: Entry) -> str:
    tags = f" [{' '.join('#' + tag for tag in entry.tags)}]" if entry.tags else ""
    why = f"\n    why: {entry.why}" if entry.why else ""
    return f"{entry.entry_id}. {entry.text}{tags}\n    at: {entry.created_at}{why}"


def format_markdown(entries: Iterable[Entry]) -> str:
    lines = ["# Pulse Log", ""]
    for entry in entries:
        tag_text = " ".join(f"`#{tag}`" for tag in entry.tags)
        suffix = f" {tag_text}" if tag_text else ""
        lines.append(f"## {entry.entry_id}. {entry.text}{suffix}")
        lines.append("")
        lines.append(f"- Created: `{entry.created_at}`")
        if entry.why:
            lines.append(f"- Why: {entry.why}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record and browse a local JSONL pulse log.")
    parser.add_argument("--file", type=Path, default=DEFAULT_LOG, help="log file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add an entry")
    add_parser.add_argument("text", help="entry text")
    add_parser.add_argument("--tag", action="append", default=[], help="tag for this entry")
    add_parser.add_argument("--why", help="short rationale or context")

    list_parser = subparsers.add_parser("list", help="list entries")
    list_parser.add_argument("--tag", help="only show entries with this tag")
    list_parser.add_argument("--limit", type=int, default=20, help="maximum entries to show")

    show_parser = subparsers.add_parser("show", help="show one entry")
    show_parser.add_argument("id", type=int, help="entry id")

    subparsers.add_parser("export-md", help="export all entries as Markdown")
    return parser


def run(argv: Sequence[str], stdout: object = sys.stdout, stderr: object = sys.stderr) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "add":
            entry = add_entry(args.file, args.text, args.tag, args.why)
            print(format_entry(entry), file=stdout)
            return 0

        entries = read_entries(args.file)
        if args.command == "list":
            selected = entries
            if args.tag:
                wanted = args.tag.strip().lower()
                selected = [entry for entry in selected if wanted in entry.tags]
            if args.limit < 1:
                print("--limit must be at least 1", file=stderr)
                return 2
            for entry in selected[-args.limit :]:
                print(format_entry(entry), file=stdout)
            return 0

        if args.command == "show":
            entry = find_entry(entries, args.id)
            if not entry:
                print(f"entry {args.id} not found", file=stderr)
                return 1
            print(format_entry(entry), file=stdout)
            return 0

        if args.command == "export-md":
            print(format_markdown(entries), end="", file=stdout)
            return 0
    except ValueError as exc:
        print(exc, file=stderr)
        return 1

    parser.error(f"unknown command: {args.command}")
    return 2


def main() -> int:
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
