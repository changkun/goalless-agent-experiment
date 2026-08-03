#!/usr/bin/env python3
"""td — a tiny, friendly task manager for your terminal.

A self-contained CLI (stdlib only) that tracks tasks with priorities,
due dates, projects, and labels. Data is persisted as JSON.

Usage:
    td add "write report" -p high -d fri @work +reporting
    td ls                 # list all tasks
    td ls @work           # filter by label
    td done 3 7           # mark tasks 3 and 7 complete
    td next               # list only open tasks, most urgent first
    td rm 2               # delete a task
    td clear              # remove all completed tasks
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import datetime as dt
from pathlib import Path

DATA_DIR = Path(os.environ.get("TD_DIR", Path.home() / ".td"))
DATA_FILE = DATA_DIR / "tasks.json"

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
PRIORITY_SYMBOL = {"critical": "!!", "high": "!", "medium": "~", "low": ".", "none": " "}
PRIORITY_COLOR = {"critical": "91", "high": "93", "medium": "96", "low": "90", "none": "0"}

NEXT_DAYS = {"today": 0, "tomorrow": 1}


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open() as fh:
        data = json.load(fh)
    # Normalize legacy/partial fields so downstream code is simple.
    for t in data:
        t.setdefault("done", False)
        t.setdefault("priority", "none")
        t.setdefault("due", None)
        t.setdefault("labels", [])
        t.setdefault("project", None)
        t.setdefault("created", dt.date.today().isoformat())
    return data


def save(tasks: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w") as fh:
        json.dump(tasks, fh, indent=2)
        fh.write("\n")
    tmp.replace(DATA_FILE)  # atomic write so a crash never corrupts data


def next_id(tasks: list[dict]) -> int:
    return max((t["id"] for t in tasks), default=0) + 1


# --------------------------------------------------------------------------- #
# Input parsing
# --------------------------------------------------------------------------- #
def parse_due(text: str) -> str | None:
    """Accept a handful of friendly due-date forms or an ISO date."""
    t = text.strip().lower()
    if not t:
        return None
    if t in NEXT_DAYS:
        return (dt.date.today() + dt.timedelta(days=NEXT_DAYS[t])).isoformat()
    if t == "tmrw" or t == "tmr":
        return (dt.date.today() + dt.timedelta(days=1)).isoformat()
    # absolute ISO (yyyy-mm-dd)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        return t
    # weekday names: "mon", "monday", "fri" -> next occurrence
    names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for i, name in enumerate(names):
        if t.startswith(name):
            today = dt.date.today()
            target = today + dt.timedelta(days=(i - today.weekday()) % 7)
            if target <= today:
                target += dt.timedelta(days=7)
            return target.isoformat()
    raise ValueError(f"Unknown due-date '{text}' (try 'today', 'fri', or 2026-08-10)")


def parse_tokens(tokens: list[str]) -> tuple[str, str | None, list[str], str | None, list[str]]:
    """Split argv tokens into (text, priority, project, due, labels)."""
    text_parts: list[str] = []
    priority = None
    project = None
    due = None
    labels: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        i += 1
        if tok.startswith("+") and len(tok) > 1:
            project = tok[1:]
        elif tok.startswith("@") and len(tok) > 1:
            labels.append(tok[1:])
        elif tok in ("-p", "--priority"):
            priority = normalize_priority(tokens[i])
            i += 1
        elif tok.startswith("-p") and len(tok) > 2:
            priority = normalize_priority(tok[2:])
        elif tok in ("-d", "--due"):
            due = parse_due(tokens[i])
            i += 1
        elif tok.startswith("-d") and len(tok) > 2:
            due = parse_due(tok[2:])
        else:
            text_parts.append(tok)
    return " ".join(text_parts), priority, project, due, labels


def normalize_priority(p: str | None) -> str:
    if p is None:
        return "none"
    if p in PRIORITY_ORDER:
        return p
    shortcuts = {"h": "high", "c": "critical", "m": "medium", "l": "low"}
    if p in shortcuts:
        return shortcuts[p]
    raise ValueError(f"Unknown priority '{p}' (critical/high/medium/low)")


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_add(args, tasks) -> int:
    text, priority, project, due, labels = parse_tokens(args.tokens)
    if not text:
        print("error: task text is required", file=sys.stderr)
        return 1
    task = {
        "id": next_id(tasks),
        "text": text,
        "done": False,
        "priority": normalize_priority(priority),
        "project": project,
        "due": due,
        "labels": labels,
        "created": dt.date.today().isoformat(),
    }
    tasks.append(task)
    save(tasks)
    print(f"added #{task['id']} {text}")
    return 0


def _find(tasks, ids) -> list[dict]:
    wanted = set(ids)
    return [t for t in tasks if t["id"] in wanted]


def cmd_done(args, tasks) -> int:
    found = _find(tasks, args.ids)
    if not found:
        print("error: no matching task id", file=sys.stderr)
        return 1
    ids = {t["id"] for t in found}
    for t in tasks:
        if t["id"] in ids:
            t["done"] = True
    save(tasks)
    print(f"completed {len(found)} task(s)")
    return 0


def cmd_rm(args, tasks) -> int:
    before = len(tasks)
    tasks[:] = [t for t in tasks if t["id"] not in set(args.ids)]
    save(tasks)
    print(f"removed {before - len(tasks)} task(s)")
    return 0


def cmd_clear(args, tasks) -> int:
    before = len(tasks)
    tasks[:] = [t for t in tasks if not t["done"]]
    save(tasks)
    print(f"cleared {before - len(tasks)} completed task(s)")
    return 0


def _filter(tasks, label: str | None, project: str | None, show_done: bool):
    if label:
        label = label.lstrip("@")  # tolerate "td ls @dev" and "td ls dev"
    out = []
    for t in tasks:
        if not show_done and t["done"]:
            continue
        if label and label not in t["labels"]:
            continue
        if project and t["project"] != project:
            continue
        out.append(t)
    return out


def _sort_key(t: dict):
    return (t["done"], PRIORITY_ORDER[t["priority"]], t.get("due") or "9999-99-99", t["id"])


def _format(t: dict, overdue: bool) -> str:
    sym = PRIORITY_SYMBOL[t["priority"]]
    color = PRIORITY_COLOR[t["priority"]]
    tick = "x" if t["done"] else " "
    due_piece = ""
    if t["due"]:
        due_piece = f"  (due {t['due']})"
        if overdue:
            due_piece += " [overdue]"
    labels = " ".join("@" + lab for lab in t["labels"])
    proj = f" +{t['project']}" if t["project"] else ""
    rest = f"{labels}{proj}"
    return (f" [{tick}] \033[{color}m{sym}\033[0m "
            f"#{t['id']:<3} {t['text']}{due_piece}{rest}")


def cmd_ls(args, tasks) -> int:
    show_done = args.all
    filtered = _filter(tasks, args.label, args.project, show_done)
    filtered.sort(key=_sort_key)
    today = dt.date.today()
    lines = []
    for i, t in enumerate(filtered, 1):
        overdue = t["due"] is not None and not t["done"] and t["due"] < today.isoformat()
        lines.append(f"{i:>2}.{_format(t, overdue)}")
    if not lines:
        print("no tasks" + ("" if show_done else " (use --all to see completed)"))
        return 0
    print("\n".join(lines))
    open_n = sum(1 for t in filtered if not t["done"])
    print(f"\n{open_n} open / {len(filtered)} shown")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="td",
        description="a tiny, friendly task manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add a task")
    a.add_argument("tokens", nargs=argparse.REMAINDER, help="task text; flags: -p <prio> -d <due> +proj @label")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("ls", help="list tasks")
    l.add_argument("label", nargs="?", default=None, help="only show tasks with this @label")
    l.add_argument("-a", "--all", action="store_true", help="include completed tasks")
    l.add_argument("--project", default=None, help="only show tasks in this +project")
    l.set_defaults(func=cmd_ls)

    l2 = sub.add_parser("next", help="list open tasks, most urgent first")
    l2.add_argument("-a", "--all", action="store_true", help="include completed tasks")
    l2.add_argument("--project", default=None, help="only show tasks in this +project")
    l2.set_defaults(func=cmd_ls, label=None)

    d = sub.add_parser("done", help="mark tasks complete")
    d.add_argument("ids", type=int, nargs="+")
    d.set_defaults(func=cmd_done)

    r = sub.add_parser("rm", help="delete tasks")
    r.add_argument("ids", type=int, nargs="+")
    r.set_defaults(func=cmd_rm)

    c = sub.add_parser("clear", help="remove completed tasks")
    c.set_defaults(func=cmd_clear)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    tasks = load()
    try:
        return args.func(args, tasks)
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    sys.exit(main())
