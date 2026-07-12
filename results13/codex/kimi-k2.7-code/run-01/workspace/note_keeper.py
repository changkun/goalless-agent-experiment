"""A tiny command-line note keeper.

Usage:
    python note_keeper.py add "Buy milk"
    python note_keeper.py list
    python note_keeper.py search milk
    python note_keeper.py delete 1

Environment:
    NOTES_FILE: path to the JSON notes file (default ~/.notes.json)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_NOTES_PATH = Path.home() / ".notes.json"


def load_notes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def save_notes(path: Path, notes: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(notes, file, indent=2, ensure_ascii=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_add(path: Path, text: str) -> int:
    notes = load_notes(path)
    note = {"id": len(notes) + 1, "text": text, "created_at": now_iso()}
    notes.append(note)
    save_notes(path, notes)
    print(f"Added note #{note['id']}: {text}")
    return 0


def cmd_list(path: Path) -> int:
    notes = load_notes(path)
    if not notes:
        print("No notes yet.")
        return 0
    for note in notes:
        print(f"#{note['id']} [{note.get('created_at', '?')}] {note['text']}")
    return 0


def cmd_search(path: Path, query: str) -> int:
    notes = load_notes(path)
    matches = [note for note in notes if query.lower() in note.get("text", "").lower()]
    if not matches:
        print("No matching notes.")
        return 0
    for note in matches:
        print(f"#{note['id']} [{note.get('created_at', '?')}] {note['text']}")
    return 0


def cmd_delete(path: Path, note_id: int) -> int:
    notes = load_notes(path)
    new_notes = [note for note in notes if note.get("id") != note_id]
    if len(new_notes) == len(notes):
        print(f"Note #{note_id} not found.", file=sys.stderr)
        return 1
    save_notes(path, new_notes)
    print(f"Deleted note #{note_id}.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Keep short notes from the command line.")
    parser.add_argument(
        "--file",
        dest="notes_file",
        type=Path,
        default=Path(os.environ.get("NOTES_FILE", DEFAULT_NOTES_PATH)),
        help="path to the notes JSON file",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add a new note")
    add_parser.add_argument("text", help="note text")

    subparsers.add_parser("list", help="list all notes")

    search_parser = subparsers.add_parser("search", help="search notes")
    search_parser.add_argument("query", help="search substring")

    delete_parser = subparsers.add_parser("delete", help="delete a note by id")
    delete_parser.add_argument("note_id", type=int, help="note id")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    match args.command:
        case "add":
            return cmd_add(args.notes_file, args.text)
        case "list":
            return cmd_list(args.notes_file)
        case "search":
            return cmd_search(args.notes_file, args.query)
        case "delete":
            return cmd_delete(args.notes_file, args.note_id)
    return 1


if __name__ == "__main__":
    sys.exit(main())
