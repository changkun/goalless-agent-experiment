"""Core analysis logic: turn raw git commit metadata into health insights."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Optional


class Commit(NamedTuple):
    """A single commit, minimally parsed from `git log` output."""

    sha: str
    author: str
    email: str
    date: datetime
    insertions: int
    deletions: int


class RepoStats(NamedTuple):
    """Aggregated, ready-to-display statistics for a repository."""

    repo_path: str
    branch: str
    total_commits: int
    first_commit: Optional[datetime]
    last_commit: Optional[datetime]
    active_days: int
    authors: Dict[str, int]               # author -> commit count
    author_emails: Dict[str, str]         # author -> most recent email
    bus_factor: int
    hotspots: List[Any]                   # list of (label, count) churn hotspots
    avg_commits_per_active_day: float
    commits_per_day: Dict[str, int]       # ISO date -> commit count (all authors)
    author_days: Dict[str, Dict[str, int]]  # author -> {ISO date -> commit count}


def iso_day(dt: datetime) -> str:
    """Return the local calendar date of a commit as an ISO string."""
    return dt.date().isoformat()


def _bus_factor(authors: Counter) -> int:
    """The minimum number of top authors most responsible for the codebase.

    Standard definition: the smallest set of authors whose commit share,
    summed together, writes at least half the commits.
    """
    total = sum(authors.values())
    if not total:
        return 0
    ordered = authors.most_common()
    acc = 0
    for index, (_, count) in enumerate(ordered, start=1):
        acc += count
        if acc * 2 >= total:
            return index
    return len(ordered)


def analyze(
    commits: List[Commit],
    *,
    repo_path: str = "",
    branch: str = "",
) -> RepoStats:
    """Compute human-readable statistics from a list of commits."""
    total = len(commits)
    commits = sorted(commits, key=lambda c: c.date)

    author_counts: Counter = Counter(c.author for c in commits)
    latest_email: Dict[str, str] = {}
    for c in commits:  # sorted ascending, so later commits overwrite earlier
        if c.author in author_counts:
            latest_email[c.author] = c.email

    active_days = len({iso_day(c.date) for c in commits})

    first = commits[0].date if commits else None
    last = commits[-1].date if commits else None

    span_days = max((last - first).days, 1) if first and last else 1
    avg_per_day = total / span_days

    days = sorted({iso_day(c.date) for c in commits})
    per_day = Counter(iso_day(c.date) for c in commits)

    author_days: Dict[str, Dict[str, int]] = {}
    for c in commits:
        bucket = author_days.setdefault(c.author, {})
        day = iso_day(c.date)
        bucket[day] = bucket.get(day, 0) + 1

    # Churn hotspots: reasons behind the most changes. Group by
    # author+day so bursts of work by one person are visible.
    hotspot_counter: Counter = Counter(
        f"{c.author} on {iso_day(c.date)}" for c in commits
    )

    return RepoStats(
        repo_path=repo_path,
        branch=branch,
        total_commits=total,
        first_commit=first,
        last_commit=last,
        active_days=active_days,
        authors=dict(
            sorted(author_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        author_emails=latest_email,
        bus_factor=_bus_factor(author_counts),
        hotspots=hotspot_counter.most_common(5),
        avg_commits_per_active_day=total / max(active_days, 1),
        commits_per_day=dict(sorted(per_day.items())),
        author_days=author_days,
    )
