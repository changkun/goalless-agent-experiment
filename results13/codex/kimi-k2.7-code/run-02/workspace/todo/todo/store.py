"""JSON-backed todo storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Task:
    id: int
    text: str
    done: bool = False


class TaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._tasks: list[Task] = []
        self._next_id = 1
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        self._tasks = [Task(**item) for item in data["tasks"]]
        self._next_id = data.get("next_id", max((t.id for t in self._tasks), default=0) + 1)

    def _save(self) -> None:
        data = {
            "next_id": self._next_id,
            "tasks": [asdict(t) for t in self._tasks],
        }
        self.path.write_text(json.dumps(data, indent=2))

    def add(self, text: str) -> Task:
        task = Task(id=self._next_id, text=text, done=False)
        self._next_id += 1
        self._tasks.append(task)
        self._save()
        return task

    def list(self, show_all: bool = False) -> list[Task]:
        if show_all:
            return list(self._tasks)
        return [t for t in self._tasks if not t.done]

    def done(self, task_id: int) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                task.done = True
                self._save()
                return task
        return None

    def remove(self, task_id: int) -> bool:
        for index, task in enumerate(self._tasks):
            if task.id == task_id:
                self._tasks.pop(index)
                self._save()
                return True
        return False
