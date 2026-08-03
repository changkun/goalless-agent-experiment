"""SQLite-backed storage for flashcards.

Uses only the Python standard library's ``sqlite3`` module. Each deck is
one database file; cards live in a single table with their SM-2 state
stored as scalar columns so queries (``due``, stats) are trivial SQL.

Day numbers are integer ``days_since_epoch`` values computed from
:func:`datetime.date.toordinal` offset, so scheduling day arithmetic is
pure integer math and independent of timezone handling.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .sm2 import CardState

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    front       TEXT NOT NULL,
    back        TEXT NOT NULL,
    ease        REAL NOT NULL DEFAULT 2.5,
    interval    INTEGER NOT NULL DEFAULT 0,
    reps        INTEGER NOT NULL DEFAULT 0,
    lapses      INTEGER NOT NULL DEFAULT 0,
    due         INTEGER NOT NULL,          -- day number it becomes due
    created     INTEGER NOT NULL
);
"""

EPOCH = date(1970, 1, 1)


def today() -> int:
    """Current day number (days since 1970-01-01)."""
    return (date.today() - EPOCH).days


# Card model: a plain dict with an optional id (None for unsaved cards).
Card = dict


class Deck:
    """A flashcard deck backed by a single sqlite file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def add(self, front: str, back: str) -> int:
        """Create a brand-new card, due immediately. Returns its id."""
        cur = self._conn.execute(
            "INSERT INTO cards (front, back, due, created) VALUES (?, ?, ?, ?)",
            (front, back, today(), today()),
        )
        self._conn.commit()
        return cur.lastrowid

    def get(self, card_id: int) -> Card | None:
        row = self._conn.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_state(self, card_id: int, state: CardState, due: int) -> None:
        """Persist a new computation state and due day for a card."""
        self._conn.execute(
            "UPDATE cards SET ease=?, interval=?, reps=?, lapses=?, due=? WHERE id=?",
            (state.ease, state.interval, state.reps, state.lapses, due, card_id),
        )
        self._conn.commit()

    def due(self, as_of: int | None = None) -> list[Card]:
        """All cards whose due day is <= ``as_of`` (default today), by id."""
        as_of = today() if as_of is None else as_of
        rows = self._conn.execute(
            "SELECT * FROM cards WHERE due <= ? ORDER BY id", (as_of,)
        ).fetchall()
        return [dict(r) for r in rows]

    def all(self) -> list[Card]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM cards ORDER BY id"
        ).fetchall()]

    def stats(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN due <= ? THEN 1 ELSE 0 END) AS due_count, "
            "SUM(lapses) AS total_lapses, "
            "ROUND(AVG(ease), 2) AS avg_ease "
            "FROM cards",
            (today(),),
        ).fetchone()
        d = dict(row)
        d["total"] = d["total"] or 0
        d["due_count"] = d["due_count"] or 0
        d["total_lapses"] = d["total_lapses"] or 0
        d["avg_ease"] = d["avg_ease"] or 0.0
        return d

    def card_state(self, card: Card) -> CardState:
        return CardState(
            ease=card["ease"],
            interval=card["interval"],
            reps=card["reps"],
            lapses=card["lapses"],
        )
