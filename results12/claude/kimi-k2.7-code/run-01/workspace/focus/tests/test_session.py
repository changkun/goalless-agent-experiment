"""Tests for focus.session."""

from datetime import datetime
from pathlib import Path

from focus.session import Session, Store, summarize, total_minutes


def test_session_roundtrip(tmp_path: Path) -> None:
    store = Store(tmp_path / "sessions.jsonl")
    session = Session(
        task="read docs",
        started_at=datetime(2026, 7, 12, 9, 0),
        duration_minutes=25,
        tags=("reading",),
    )
    store.add(session)
    assert store.sessions() == [session]


def test_summarize_groups_by_tag() -> None:
    sessions = [
        Session("coding", datetime.now(), 30, ("dev",)),
        Session("more coding", datetime.now(), 20, ("dev", "claude")),
        Session("email", datetime.now(), 10, ()),
    ]
    assert summarize(sessions) == {"dev": 50, "claude": 20, "untagged": 10}


def test_total_minutes() -> None:
    sessions = [
        Session("a", datetime.now(), 10, ()),
        Session("b", datetime.now(), 5, ()),
    ]
    assert total_minutes(sessions) == 15
