"""Pocket: a tiny, dependency-free notes and tasks manager stored in Markdown.

Everything lives in a single Markdown file (the "journal"). Days are H2
sections; notes are bullets; tasks are "- [ ] / - [x]" checkboxes. Parsing is
line-based so the file stays human-readable and editable by hand.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from dataclasses import dataclass
from typing import Optional


def _today() -> str:
    return _dt.date.today().isoformat()


def default_path() -> str:
    """Return the default journal path, honouring an env override."""
    return os.environ.get("POCKET_FILE", os.path.expanduser("~/.pocket.md"))


@dataclass
class Note:
    text: str
    date: str
    task: bool = False
    done: bool = False
    index: int = -1  # chronological position among all items in the file


_SECTION_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})$")
_TASK_RE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.+)$")
_ITEM_RE = re.compile(r"^\s*-\s+(.+)$")


def _section(line: str) -> Optional[str]:
    m = _SECTION_RE.match(line)
    return m.group(1) if m else None


def _parse_item(line: str) -> Optional[Note]:
    m = _TASK_RE.match(line)
    if m:
        return Note(text=m.group(2).strip(), date="", task=True, done=m.group(1) in "xX")
    m = _ITEM_RE.match(line)
    if m:
        return Note(text=m.group(1).strip(), date="", task=False, done=False)
    return None


def render(note: Note) -> str:
    if note.task:
        return f"- [{'x' if note.done else ' '}] {note.text}"
    return f"- {note.text}"


def read(file: str) -> list[Note]:
    """Return all notes/tasks newest-first, with dates applied."""
    notes: list[Note] = []
    current = ""
    idx = 0
    if not os.path.exists(file):
        return notes
    with open(file, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            sec = _section(line)
            item = _parse_item(line)
            if sec:
                current = sec
            elif item:
                item.date = current
                item.index = idx
                idx += 1
                notes.append(item)
    # Newest date first, and within a day the most recently added first.
    notes.sort(key=lambda n: (n.date, n.index))
    notes.reverse()
    return notes


def _ensure_day(file: str, date: str) -> None:
    """Create the file skeleton if absent, and add a day section if missing."""
    lines: list[str] = []
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    if not lines:
        lines = ["# Pocket Journal", ""]
    if not any(_section(l) == date for l in lines):
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"## {date}")
    with open(file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def add(file: str, text: str, *, task: bool = False, done: bool = False) -> Note:
    date = _today()
    _ensure_day(file, date)
    note = Note(text=text, date=date, task=task, done=done)
    with open(file, "a", encoding="utf-8") as fh:
        fh.write(render(note) + "\n")
    return note


def list_items(file: str, *, kind: str = "all", days: Optional[int] = None,
               limit: Optional[int] = None) -> list[Note]:
    """Return items filtered by kind (all/notes/tasks) and recency."""
    notes = read(file)
    if kind == "tasks":
        notes = [n for n in notes if n.task]
    elif kind == "notes":
        notes = [n for n in notes if not n.task]
    if days is not None:
        cutoff = _dt.date.today() - _dt.timedelta(days=days)
        notes = [n for n in notes if n.date >= cutoff.isoformat()]
    return notes[:limit] if limit else notes


def _rewrite_item(file: str, target_idx: int, replace: Optional[str]) -> None:
    """Rewrite the journal, replacing/removing the item at chronological index."""
    with open(file, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    new_lines: list[str] = []
    item_pos = 0
    for line in lines:
        item = _parse_item(line)
        if item is not None:
            if item_pos == target_idx:
                if replace is not None:
                    new_lines.append(replace)
                item_pos += 1
                continue
            item_pos += 1
        new_lines.append(line)
    with open(file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines) + "\n")


def set_done(file: str, index: int, done: bool) -> Optional[Note]:
    """Set completion of the Nth item (0-based, newest-first) in place."""
    all_notes = read(file)
    if index < 0 or index >= len(all_notes):
        return None
    target = all_notes[index]
    note = Note(text=target.text, date=target.date, task=target.task, done=done)
    _rewrite_item(file, target.index, render(note))
    return note


def remove(file: str, index: int) -> Optional[Note]:
    """Delete the Nth item (0-based, newest-first) from the journal."""
    all_notes = read(file)
    if index < 0 or index >= len(all_notes):
        return None
    target = all_notes[index]
    _rewrite_item(file, target.index, None)
    return target
