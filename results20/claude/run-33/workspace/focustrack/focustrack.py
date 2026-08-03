#!/usr/bin/env python3
"""focustrack — a tiny focus-session tracker.

Records focus sessions (project, tags, notes), stores them in a local JSON
file, and can summarize your day/week, list sessions, and export to Markdown.

Usage (see `focustrack.py --help` for the full list):

    # Start timing a session. Ctrl+C ends it and prompts for tags/notes.
    focustrack.py start         --project "Docs" --tag writing --tag research

    # Record a finished session whose length you already know.
    focustrack.py add --minutes 45 --project "Docs" --tag writing --note "draft"

    # Look back.
    focustrack.py today
    focustrack.py week
    focustrack.py list --limit 10
    focustrack.py export --out sessions.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_DB = "~/.focustrack.json"


# --------------------------------------------------------------------------
# Data layer
# --------------------------------------------------------------------------
class Store:
    """Thin JSON wrapper. One session per record."""

    FIELDS = ("id", "project", "tags", "note", "started", "ended", "minutes")

    def __init__(self, path: str):
        self.path = Path(path).expanduser()
        self._sessions: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            print(f"warning: could not read {self.path}; starting empty", file=sys.stderr)
            return
        self._sessions = data if isinstance(data, list) else []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._sessions, indent=2) + "\n")

    def add(self, session: dict) -> dict:
        session = {k: session.get(k) for k in self.FIELDS}
        session["id"] = session.get("id") or self._next_id()
        self._sessions.append(session)
        self.save()
        return session

    def _next_id(self) -> int:
        return max((s.get("id", 0) for s in self._sessions), default=0) + 1

    def all(self) -> list[dict]:
        return sorted(self._sessions, key=lambda s: s.get("started", ""))

    def since(self, start: datetime, end: datetime) -> list[dict]:
        out = []
        for s in self._sessions:
            started = _parse_dt(s.get("started"))
            if started is None:
                continue
            if start <= started < end:
                out.append(s)
        return out


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day)
    return start, start + timedelta(days=1)


def _fmt_duration(total_minutes: int) -> str:
    total_minutes = int(total_minutes)
    h, m = divmod(total_minutes, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def _tag_color(tag: str) -> str:
    """Deterministic-ish ANSI palette keyed off the tag so repeats look stable."""
    palette = ["36", "35", "33", "32", "31", "34", "96", "95"]
    idx = sum(ord(c) for c in tag) % len(palette)
    return palette[idx]


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def _stat_line(store: Store, start: datetime, end: datetime) -> str:
    sessions = store.since(start, end)
    total = sum(s.get("minutes", 0) for s in sessions)
    by_proj = Counter(s.get("project") or "?" for s in sessions)
    top = ", ".join(f"{p} {_fmt_duration(m)}" for p, m in by_proj.most_common(5))
    return f"{len(sessions)} session(s) · {_fmt_duration(total)} total" + (
        f"  |  {top}" if top else ""
    )


def cmd_start(store: Store, args) -> int:
    project = args.project
    tags = args.tag or []
    if not sys.stdin.isatty():
        print("start: interactive Ctrl+C timer needs a terminal", file=sys.stderr)
        return 2
    print(f"focusing{(' on ' + project) if project else ''}" + f" [{', '.join(tags)}]" if tags else "")
    print("started at", datetime.now().strftime("%H:%M:%S"), "— Ctrl+C to end and save.")
    begin = datetime.now()
    try:
        while True:
            elapsed = int((datetime.now() - begin).total_seconds())
            sys.stdout.write(
                f"\r  elapsed: {_fmt_duration(elapsed // 60)}"
                + f" ({elapsed}s)".rjust(6)
                + "   "
            )
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print()  # newline after the timer
        ended = datetime.now()
        minutes = max(1, round((ended - begin).total_seconds() / 60))
        session = store.add(
            {
                "project": project,
                "tags": tags,
                "note": args.note,
                "started": _iso(begin),
                "ended": _iso(ended),
                "minutes": minutes,
            }
        )
        print(f"saved #{session['id']}: {_fmt_duration(minutes)} on "
              f"{session['project'] or '(no project)'}."
              f" Edit ~/.focustrack.json to add tags/notes.")
        return 0


def cmd_add(store: Store, args) -> int:
    if not args.minutes:
        print("add: --minutes is required", file=sys.stderr)
        return 2
    minutes = args.minutes
    # start/end are best-effort; if only minutes given, backdate "now".
    end = _parse_dt(args.end) or datetime.now()
    start = _parse_dt(args.start) or (end - timedelta(minutes=minutes))
    if (end - start).total_seconds() / 60 < minutes:
        start = end - timedelta(minutes=minutes)
    session = store.add(
        {
            "project": args.project,
            "tags": args.tag or [],
            "note": args.note,
            "started": _iso(start),
            "ended": _iso(end),
            "minutes": minutes,
        }
    )
    print(f"saved #{session['id']}: {_fmt_duration(minutes)} on "
          f"{session['project'] or '(no project)'} with tags "
          f"{', '.join(session['tags']) or '(none)'}.")
    return 0


def cmd_today(store: Store, args) -> int:
    start, end = _day_bounds(date.today())
    _print_block(store, start, end)
    return 0


def cmd_week(store: Store, args) -> int:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start, end = _day_bounds(monday)
    _print_block(store, start, end)
    return 0


def _print_block(store: Store, start: datetime, end: datetime) -> None:
    sessions = store.since(start, end)
    print(f"=== {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} ===")
    print(_stat_line(store, start, end))
    if not sessions:
        print("(nothing recorded)")
        return
    for s in sorted(sessions, key=lambda x: x.get("started", "")):
        started = _parse_dt(s.get("started"))
        clock = started.strftime("%H:%M") if started else "  --:-- "
        tags = " ".join(
            f"\033[{_tag_color(t)}m#{t}\033[0m" for t in (s.get("tags") or [])
        )
        note = f"  \033[90m— {s['note']}\033[0m" if s.get("note") else ""
        print(f"  {clock}  {_fmt_duration(s['minutes']):>5}  "
              f"{s.get('project') or '(no project)':<14} {tags}{note}")


def cmd_list(store: Store, args) -> int:
    sessions = store.all()
    limit = args.limit or len(sessions)
    for s in sessions[-limit:]:
        started = _parse_dt(s.get("started"))
        clock = started.strftime("%Y-%m-%d %H:%M") if started else "(no time)"
        tags = ",".join(s.get("tags") or [])
        note = f"  — {s['note']}" if s.get("note") else ""
        print(f"#{s['id']:<4} {clock}  {_fmt_duration(s['minutes']):>5}  "
              f"{s.get('project') or '(no project)':<14} [{tags}]{note}")
    return 0


def _summary(store: Store, start: datetime, end: datetime) -> dict:
    sessions = store.since(start, end)
    per_day: dict[str, int] = defaultdict(int)
    per_proj: dict[str, int] = defaultdict(int)
    tag_total: dict[str, int] = defaultdict(int)
    for s in sessions:
        day = (_parse_dt(s.get("started")) or end).strftime("%Y-%m-%d")
        per_day[day] += s.get("minutes", 0)
        per_proj[s.get("project") or "(none)"] += s.get("minutes", 0)
        for t in s.get("tags") or []:
            tag_total[t] += s.get("minutes", 0)
    return {
        "sessions": len(sessions),
        "total_minutes": sum(s.get("minutes", 0) for s in sessions),
        "per_day": dict(sorted(per_day.items())),
        "per_proj": per_proj,
        "per_tag": dict(sorted(tag_total.items(), key=lambda x: -x[1])),
    }


def cmd_summary(store: Store, args) -> int:
    end = datetime.now()
    start = end - timedelta(days=args.days)
    s = _summary(store, start, end)

    label = f"last {args.days} days ({start.date()} → {end.date()})"
    print(f"=== Summary: {label} ===")
    print(s["sessions"], "sessions ·", _fmt_duration(s["total_minutes"]))
    print("\nby project:")
    for p, m in sorted(s["per_proj"].items(), key=lambda x: -x[1]):
        bar = "#" * max(1, int(30 * m / max(1, s["total_minutes"])))
        print(f"  {p:<14} {_fmt_duration(m):>6}  {bar}")
    print("\nby day:")
    for d, m in s["per_day"].items():
        print(f"  {d}  {_fmt_duration(m)}")
    if s["per_tag"]:
        print("\nby tag:")
        for t, m in s["per_tag"].items():
            print(f"  {t:<12} {_fmt_duration(m)}")
    return 0


def cmd_export(store: Store, args) -> int:
    start, end = _day_bounds(date.today())
    name = args.name or "Untitled"
    assert name and not any(c in name for c in ('/', '\\'))
    s = _summary(store, start, end)

    lines = [
        f"# {name} — {start.date()}",
        "",
        f"**{s['sessions']} sessions · {_fmt_duration(s['total_minutes'])}**",
        "",
        "## By project",
        "",
    ]
    for p, m in sorted(s["per_proj"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{p}**: {_fmt_duration(m)}")
    lines += ["", "## Sessions", ""]
    for sess in sorted(store.since(start, end), key=lambda x: x.get("started", "")):
        started = _parse_dt(sess.get("started"))
        clock = started.strftime("%H:%M") if started else "--:--"
        tags = ", ".join(sess.get("tags") or [])
        note = f" — {sess['note']}" if sess.get("note") else ""
        lines.append(f"- `{clock}` {_fmt_duration(sess['minutes'])} "
                     f"**{sess.get('project') or '(no project)'}** [{tags}]{note}")
    body = "\n".join(lines) + "\n"

    out = args.out
    if out and out != "-":
        Path(out).write_text(body)
        print(f"exported {s['sessions']} sessions → {out}")
    else:
        sys.stdout.write(body)
    return 0


# --------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="focustrack",
        description="Track focus sessions and review how you spend your time.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--db", default=DEFAULT_DB, help="path to the JSON store")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("start", help="begin an interactive timed session")
    sp.add_argument("--project", "-p")
    sp.add_argument("--tag", "-t", action="append", default=[])
    sp.add_argument("--note", "-n")

    sp = sub.add_parser("add", help="record a finished session")
    sp.add_argument("--minutes", "-m", type=int)
    sp.add_argument("--project", "-p")
    sp.add_argument("--tag", "-t", action="append", default=[])
    sp.add_argument("--note", "-n")
    sp.add_argument("--start")
    sp.add_argument("--end")

    sub.add_parser("today", help="show today's sessions")
    sub.add_parser("week", help="show this week's sessions")
    sp = sub.add_parser("list", help="list recent sessions")
    sp.add_argument("--limit", "-n", type=int)

    sp = sub.add_parser("summary", help="summarize a trailing window")
    sp.add_argument("--days", type=int, default=7)

    sp = sub.add_parser("export", help="write the day as markdown")
    sp.add_argument("--out", "-o")
    sp.add_argument("--name", default="Focus log")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    store = Store(args.db)
    fn = {
        "start": cmd_start,
        "add": cmd_add,
        "today": cmd_today,
        "week": cmd_week,
        "list": cmd_list,
        "summary": cmd_summary,
        "export": cmd_export,
    }.get(args.cmd)
    if fn is None:
        print("unknown command", file=sys.stderr)
        return 2
    return fn(store, args)


if __name__ == "__main__":
    sys.exit(main())
