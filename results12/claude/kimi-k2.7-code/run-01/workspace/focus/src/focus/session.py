"""Core logic for recording and summarizing focus sessions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Session:
    """A single uninterrupted focus block."""

    task: str
    started_at: datetime
    duration_minutes: int
    tags: tuple[str, ...] = field(default_factory=tuple)

    def ended_at(self) -> datetime:
        return self.started_at + timedelta(minutes=self.duration_minutes)

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "started_at": self.started_at.isoformat(),
            "duration_minutes": self.duration_minutes,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            task=data["task"],
            started_at=datetime.fromisoformat(data["started_at"]),
            duration_minutes=data["duration_minutes"],
            tags=tuple(data.get("tags", [])),
        )


class Store:
    """Append-only JSONL store for sessions."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def add(self, session: Session) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(session.to_dict()) + "\n")

    def sessions(self) -> list[Session]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return [Session.from_dict(json.loads(line)) for line in f if line.strip()]


def today(session: Session) -> bool:
    return session.started_at.date() == datetime.now().date()


def total_minutes(sessions: Iterable[Session]) -> int:
    return sum(s.duration_minutes for s in sessions)


def summarize(sessions: Iterable[Session]) -> dict[str, int]:
    """Return total minutes grouped by tag; untagged sessions go under 'untagged'."""
    result: dict[str, int] = {}
    for s in sessions:
        if s.tags:
            for tag in s.tags:
                result[tag] = result.get(tag, 0) + s.duration_minutes
        else:
            result["untagged"] = result.get("untagged", 0) + s.duration_minutes
    return result
