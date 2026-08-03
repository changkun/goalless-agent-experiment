"""Command-line interface for gitpulse."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Optional

from . import __version__
from .analyzer import RepoStats, analyze
from .errors import GitPulseError
from .git import current_branch, is_repo, load_commits

_SPARK = "▁▂▃▄▅▆▇█"


def _spark(value: float, max_value: float) -> str:
    """Map a value onto a single 8-level sparkline character."""
    if max_value <= 0:
        return "·"
    ratio = min(value / max_value, 1.0)
    index = min(round(ratio * 8) - 1, 7)
    return _SPARK[index]


def _age(before: Optional[datetime], after: Optional[datetime]) -> str:
    """Describe the time between two dates in a compact way."""
    if before is None or after is None:
        return "—"
    days = (after - before).days
    if days < 1:
        return "today"
    if days < 60:
        return f"{days}d"
    weeks = days / 7
    if weeks < 52:
        return f"{weeks:.0f}w"
    return f"{days / 365.2:.1f}y"


def _table_header() -> str:
    return f"{'author':<24} {'commits':>7} {'share':>6}  activity (last 8 active days)"


def _author_row(name: str, count: int, total: int, author_days, all_days) -> str:
    """One table row: per-author commit share plus that author's own sparkline."""
    share = count / total * 100 if total else 0
    own = author_days.get(name, {})
    peak = max(own.values()) if own else 0
    days = [d for d in sorted(all_days) if d in own][-8:] or [d for d in sorted(all_days)][-8:]
    if not days:
        cells = "·" * 8
    else:
        cells = "".join(_spark(own.get(d, 0), peak) for d in days)
    return f"{name:<24} {count:>7} {share:>5.1f}%  {cells}"


def _hotspot_text(hotspots, total: int) -> str:
    if not hotspots:
        return "  no commits yet"
    lines = []
    for label, count in hotspots:
        share = count / total * 100
        lines.append(f"  {label}  ({count} commits, {share:.0f}%)")
    return "\n".join(lines)


def format_report(stats: RepoStats) -> str:
    """Render a RepoStats object as a readable terminal report."""
    total = stats.total_commits
    days = stats.commits_per_day

    out: list[str] = []
    out.append(f"gitpulse {__version__}  —  {stats.repo_path}  ({stats.branch})")
    out.append("=" * 72)

    if total == 0:
        out.append("No commits found on this branch.")
        return "\n".join(out)

    span = (
        f"{stats.first_commit:%Y-%m-%d} → {stats.last_commit:%Y-%m-%d}"
        if stats.first_commit and stats.last_commit
        else "—"
    )
    out.append(f"Commits          {total}")
    out.append(f"Active days      {stats.active_days}")
    out.append(f"Commit span      {span}")
    out.append(
        f"Pace             {stats.avg_commits_per_active_day:.2f} commits/active day "
        f"({total / max((stats.last_commit - stats.first_commit).days, 1):.2f}/day overall)"
        if stats.first_commit and stats.last_commit
        else f"Pace             —"
    )
    out.append(f"Bus factor       {stats.bus_factor}")
    out.append("")

    out.append(_table_header())
    all_days = list(stats.commits_per_day.keys())
    for name, count in list(stats.authors.items())[:12]:
        out.append(_author_row(name, count, total, stats.author_days, all_days))
    if len(stats.authors) > 12:
        out.append(f"  … and {len(stats.authors) - 12} more")

    out.append("")
    out.append(f"Churn hotspots (top 5 of {len(stats.hotspots)})")
    out.append(_hotspot_text(stats.hotspots, total))
    out.append("")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitpulse",
        description="Quick health check for a git repository.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="path to the repository (default: current directory)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="only consider the most recent N commits",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"gitpulse {__version__}",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.path

    try:
        if not is_repo(path):
            raise GitPulseError(f"{path!r} is not inside a git working tree")
        branch = current_branch(path)
        commits = load_commits(path, limit=args.limit)
        stats = analyze(commits, repo_path=path, branch=branch)
    except GitPulseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(format_report(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
