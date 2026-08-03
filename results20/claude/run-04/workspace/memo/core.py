"""Core storage + query logic for memo.

Design notes
------------
- One JSON file, a list of entries. Simple and portable.
- An entry is a dict: {id, ts, text, tags}.
- Tag querying supports AND (all tags present) and prefix matches
  ("work" matches "work/deep") so tags can form a lightweight hierarchy.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional

_TAG_RE = re.compile(r"([a-zA-Z0-9][a-zA-Z0-9_./-]*)")

# A fresh 64-bit id: monotonic-ish time in ms shifted left, plus a counter.
_id_state = [0]


def _next_id() -> int:
    _id_state[0] = (_id_state[0] + 1) & 0x3FFFFF
    return (int(time.time() * 1000) << 22) | _id_state[0]


class MemoError(Exception):
    """Raised for user-facing errors (bad file, bad query, etc.)."""


def parse_tags(text: str) -> List[str]:
    """Extract unique, lowercased `#tag`s from text, preserving order."""
    seen: set = set()
    out: List[str] = []
    for match in _TAG_RE.finditer(text):
        raw = match.group(1)
        if text[max(0, match.start() - 1)] != "#":
            continue  # not a leading-# tag
        tag = raw.lower()
        if tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


@dataclass
class Memo:
    id: int
    ts: float
    text: str
    tags: List[str]

    def match(self, tags: Iterable[str], prefix: bool = False) -> bool:
        """True if this memo has *all* the given tags.

        With `prefix=True`, a memo matches a query tag when any of its own
        tags starts with the query tag (e.g. query "work" hits "work/deep").
        """
        have = set(self.tags)
        for t in tags:
            if prefix:
                if not any(own.startswith(t) for own in have):
                    return False
            else:
                if t not in have:
                    return False
        return True


class MemoStore:
    def __init__(self, path: str):
        self.path = path

    # -- persistence ------------------------------------------------------

    def _load(self) -> List[Memo]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise MemoError(f"cannot read {self.path}: {exc}") from exc
        out: List[Memo] = []
        for item in data:
            try:
                out.append(
                    Memo(
                        id=int(item["id"]),
                        ts=float(item["ts"]),
                        text=str(item["text"]),
                        tags=[str(t) for t in item.get("tags", [])],
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise MemoError(
                    f"corrupt entry in {self.path}: {exc!r}"
                ) from exc
        return out

    def _save(self, entries: List[Memo]) -> None:
        data = [
            {"id": m.id, "ts": m.ts, "text": m.text, "tags": m.tags}
            for m in entries
        ]
        # Atomic write: temp file in the same dir, then rename.
        directory = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp, self.path)
        except OSError:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # -- mutation ---------------------------------------------------------

    def add(self, text: str, ts: Optional[float] = None) -> Memo:
        text = text.strip()
        if not text:
            raise MemoError("memo text cannot be empty")
        memo = Memo(
            id=_next_id(),
            ts=float(ts) if ts is not None else time.time(),
            text=text,
            tags=parse_tags(text),
        )
        entries = self._load()
        entries.append(memo)
        self._save(entries)
        return memo

    def delete(self, memo_id: int) -> bool:
        entries = self._load()
        kept = [m for m in entries if m.id != memo_id]
        if len(kept) == len(entries):
            return False
        self._save(kept)
        return True

    def import_text(self, lines) -> int:
        """Bulk import: one memo per non-blank line. Returns count added."""
        count = 0
        for line in lines:
            line = str(line).strip()
            if line:
                self.add(line)
                count += 1
        return count

    # -- query ------------------------------------------------------------

    def all(self) -> List[Memo]:
        return self._load()

    def search(self, tags: Iterable[str] = (), prefix: bool = False) -> List[Memo]:
        tags = list(tags)
        entries = self._load()
        if tags:
            entries = [m for m in entries if m.match(tags, prefix=prefix)]
        # Newest first.
        entries.sort(key=lambda m: m.ts, reverse=True)
        return entries

    def tags(self) -> List[str]:
        """All tags seen, most frequent first."""
        counts: dict = {}
        for m in self._load():
            for t in m.tags:
                counts[t] = counts.get(t, 0) + 1
        return [t for t, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


# --------------------------------------------------------------------------
# Convenience: build a date-stamped seed so the tool is fun on first run.
# --------------------------------------------------------------------------

def _today_stamp() -> str:
    return time.strftime("%Y-%m-%d")


def seed_if_empty(store: MemoStore) -> int:
    """Populate an empty store with a few dated starter memos. Returns 0 if
    the store already had content, else the number seeded."""
    if store._load():
        return 0
    day = _today_stamp()
    n = store.import_text(
        [
            f"#hello Welcome to memo — a #local, no-cloud journal. {day}",
            f"Type `memo help` to see commands. #README",
        ]
    )
    return n
