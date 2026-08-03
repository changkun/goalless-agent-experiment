"""Task store for the terminal todo app.

A task is represented as a plain dict with the following keys:

- ``id``:   unique integer identifier
- ``title``: the task description (non-empty)
- ``done``:  bool, whether the task is completed
- ``priority``: one of ``low``, ``normal``, ``high``
- ``due``:   optional ``YYYY-MM-DD`` date string, or ``None``

Tasks are persisted as JSON. A newline-delimited format is deliberately
*not* used here; a plain list in a single JSON file keeps the file readable
and simple to edit by hand.
"""
from __future__ import annotations

import json
import re
import tempfile
from datetime import date
from pathlib import Path

PRIORITIES = ("low", "normal", "high")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DEFAULT_FILE = Path("todo.json")


class TodoError(Exception):
    """Raised for user-facing validation or storage errors."""


def _validate_priority(priority: str | None) -> str:
    if priority is None:
        return "normal"
    value = priority.lower()
    if value not in PRIORITIES:
        raise TodoError(
            f"invalid priority {priority!r}; choose from {', '.join(PRIORITIES)}"
        )
    return value


def _validate_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise TodoError("task title cannot be empty")
    return title


def _validate_due(due: str | None) -> str | None:
    if due is None or due == "":
        return None
    if not _DATE_RE.match(due):
        raise TodoError(f"invalid due date {due!r}; expected YYYY-MM-DD")
    return due


def _next_id(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else []
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    if isinstance(data, list) and data:
        return max(t.get("id", 0) for t in data if isinstance(t, dict)) + 1
    return 1


def _write(path: Path, tasks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically so a crash never leaves a truncated file behind.
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as fh:
            json.dump(tasks, fh, indent=2)
            fh.write("\n")
        Path(tmp_name).replace(path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class Store:
    """Loads, mutates and persists a list of tasks."""

    def __init__(self, path: str | Path = DEFAULT_FILE):
        self.path = Path(path)

    def _load(self) -> list[dict]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        if not text.strip():
            return []
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TodoError(f"could not parse {self.path}: {exc}") from exc
        if not isinstance(data, list):
            raise TodoError(f"invalid task file {self.path}: expected a list")
        return [t for t in data if isinstance(t, dict)]

    def add(self, title: str, priority: str | None = None, due: str | None = None) -> dict:
        title = _validate_title(title)
        priority = _validate_priority(priority)
        due = _validate_due(due)
        tasks = self._load()
        task = {
            "id": _next_id(self.path),
            "title": title,
            "done": False,
            "priority": priority,
            "due": due,
        }
        tasks.append(task)
        _write(self.path, tasks)
        return task

    def list_all(self, filter_done: bool | None = None) -> list[dict]:
        tasks = self._load()
        if filter_done is not None:
            tasks = [t for t in tasks if t.get("done") is filter_done]
        return tasks

    def _find(self, task_id: int) -> tuple[list[dict], dict]:
        tasks = self._load()
        for task in tasks:
            if task.get("id") == task_id:
                return tasks, task
        raise TodoError(f"no task with id {task_id}")

    def set_done(self, task_id: int, done: bool = True) -> dict:
        tasks, task = self._find(task_id)
        task["done"] = bool(done)
        _write(self.path, tasks)
        return task

    def update(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | None = None,
        due: str | None = None,
    ) -> dict:
        tasks, task = self._find(task_id)
        if title is not None:
            task["title"] = _validate_title(title)
        if priority is not None:
            task["priority"] = _validate_priority(priority)
        if due is not None:
            task["due"] = _validate_due(due)
        _write(self.path, tasks)
        return task

    def clear_done(self) -> int:
        tasks = self._load()
        remaining = [t for t in tasks if not t.get("done")]
        removed = len(tasks) - len(remaining)
        _write(self.path, remaining)
        return removed

    def delete(self, task_id: int) -> dict:
        tasks, _ = self._find(task_id)
        task = next(t for t in tasks if t.get("id") == task_id)
        remaining = [t for t in tasks if t.get("id") != task_id]
        _write(self.path, remaining)
        return task


def sort_key(task: dict) -> tuple:
    """Sort order: open first, then high priority, then due date, then id."""
    rank = {"high": 0, "normal": 1, "low": 2}
    return (
        task.get("done", False),
        rank.get(task.get("priority"), 1),
        task.get("due") or "9999-12-31",
        task.get("id", 0),
    )


def format_task(task: dict, show_due: bool = True) -> str:
    mark = "[x]" if task.get("done") else "[ ]"
    parts = [f"#{task.get('id')}", mark, task.get("title", "")]
    tags = [f"({task.get('priority', 'normal')})"]
    if show_due and task.get("due"):
        due = task["due"]
        if due < date.today().isoformat() and not task.get("done"):
            tags.append(f"due {due} (overdue)")
        else:
            tags.append(f"due {due}")
    if tags:
        parts.append(" ".join(tags))
    return " ".join(parts)
