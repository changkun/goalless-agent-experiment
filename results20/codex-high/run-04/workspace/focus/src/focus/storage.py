"""Task storage backed by a JSON file in the user's config directory."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

FOCUS_DIR_ENV = "FOCUS_DIR"
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"


def default_data_dir() -> Path:
    """Return the directory where focus stores its state."""
    env = os.environ.get(FOCUS_DIR_ENV)
    if env:
        return Path(env)
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "focus"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "focus"


@dataclass
class Task:
    id: int
    title: str
    status: str = STATUS_OPEN
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    pomodoros: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "pomodoros": self.pomodoros,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        return cls(
            id=int(data.get("id", 0)),
            title=data.get("title", ""),
            status=data.get("status", STATUS_OPEN),
            created_at=float(data.get("created_at", 0.0)),
            completed_at=data.get("completed_at"),
            pomodoros=int(data.get("pomodoros", 0)),
            tags=list(data.get("tags", [])),
        )


class TaskStore:
    """Persist tasks to JSON atomically."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (default_data_dir() / "tasks.json")
        self._tasks: List[Task] = []
        self._next_id: int = 1
        self._load()

    @property
    def tasks(self) -> List[Task]:
        return self._tasks

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        data = raw if isinstance(raw, list) else raw.get("tasks", [])
        self._tasks = [Task.from_dict(item) for item in data if isinstance(item, dict)]
        self._next_id = max((t.id for t in self._tasks), default=0) + 1

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tasks": [t.to_dict() for t in self._tasks]}
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def add(self, title: str, tags: List[str]) -> Task:
        task = Task(
            id=self._next_id,
            title=title,
            tags=sorted({t.strip() for t in tags if t.strip()}),
        )
        self._next_id += 1
        self._tasks.append(task)
        return task

    def get(self, task_id: int) -> Task | None:
        return next((t for t in self._tasks if t.id == task_id), None)

    def open_tasks(self) -> List[Task]:
        return [t for t in self._tasks if t.status == STATUS_OPEN]

    def close(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None or task.status == STATUS_CLOSED:
            return False
        task.status = STATUS_CLOSED
        task.completed_at = time.time()
        return True

    def reopen(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None or task.status != STATUS_CLOSED:
            return False
        task.status = STATUS_OPEN
        task.completed_at = None
        return True

    def remove(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True

    def clear_closed(self) -> int:
        count = len([t for t in self._tasks if t.status == STATUS_CLOSED])
        self._tasks = [t for t in self._tasks if t.status != STATUS_CLOSED]
        return count

    def add_pomodoro(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False
        task.pomodoros += 1
        return True
