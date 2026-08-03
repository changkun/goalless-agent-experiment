"""Core task store backed by a JSON file."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Task:
    id: str
    title: str
    done: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            done=data.get("done", False),
            created_at=data.get("created_at", time.time()),
        )


class TaskStore:
    """A simple JSON-backed store for tasks."""

    def __init__(self, path: str | os.PathLike[str] = "tasks.json"):
        self.path = Path(path)
        self.data: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.data = {}
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.data = {}
            return
        self.data = {
            key: value for key, value in raw.items() if isinstance(value, dict)
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=True)
            fh.write("\n")

    def add(self, title: str, done: bool = False) -> Task:
        task_id = uuid.uuid4().hex[:12]
        while task_id in self.data:
            task_id = uuid.uuid4().hex[:12]
        task = Task(id=task_id, title=title, done=done)
        self.data[task_id] = task.to_dict()
        self.save()
        return task

    def get(self, task_id: str) -> Task | None:
        raw = self.data.get(task_id)
        return Task.from_dict(raw) if raw else None

    def all(self) -> list[Task]:
        tasks = [Task.from_dict(raw) for raw in self.data.values()]
        tasks.sort(key=lambda t: (t.done, t.created_at))
        return tasks

    def set_done(self, task_id: str, done: bool) -> Task | None:
        task = self.get(task_id)
        if task is None:
            return None
        task.done = done
        self.data[task_id] = task.to_dict()
        self.save()
        return task

    def remove(self, task_id: str) -> bool:
        if task_id not in self.data:
            return False
        del self.data[task_id]
        self.save()
        return True

    def clear(self) -> None:
        self.data = {}
        self.save()
