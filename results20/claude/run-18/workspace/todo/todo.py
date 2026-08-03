#!/usr/bin/env python3
"""todo.py — a zero-dependency, single-file command-line task manager.

Usage examples:
    ./todo.py add "Write the report" -p high -d 2026-08-10 -t work -t urgent
    ./todo.py add "Buy milk" -p low
    ./todo.py list                  # all open tasks
    ./todo.py list --done           # completed tasks
    ./todo.py list -t work          # filter by tag
    ./todo.py list -s high          # filter by status/priority
    ./todo.py done 3                # mark task 3 done
    ./todo.py undo 3                # reopen task 3
    ./todo.py rm 3                  # delete task 3
    ./todo.py edit 3 "New title"
    ./todo.py purge                 # delete all completed tasks
    ./todo.py stats                 # summary counts

Data is stored as JSON in ~/.todo.json.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime

STORAGE = os.path.join(os.path.expanduser("~"), ".todo.json")
PRIORITIES = {"low", "medium", "high"}


def load():
    if not os.path.exists(STORAGE):
        return []
    with open(STORAGE) as f:
        return json.load(f)


def save(tasks):
    tmp = STORAGE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(tasks, f, indent=2, default=str)
    os.replace(tmp, STORAGE)


def next_id(tasks):
    return (max((t["id"] for t in tasks), default=0)) + 1


def get(tasks, raw_id):
    try:
        iid = int(raw_id)
    except ValueError:
        sys.exit(f"error: '{raw_id}' is not a valid task id")
    for t in tasks:
        if t["id"] == iid:
            return t, iid
    sys.exit(f"error: no task with id {raw_id}")


def parse_date(raw):
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        sys.exit(f"error: '{raw}' is not a valid date (use YYYY-MM-DD)")


def cmd_add(args):
    tasks = load()
    if not args.title:
        sys.exit("error: a title is required (quote it, e.g. add \"Write report\")")
    due = parse_date(args.due)
    if due and due < date.today():
        print(f"note: due date {args.due} is in the past")
    task = {
        "id": next_id(tasks),
        "title": args.title,
        "priority": args.priority,
        "due": args.due,
        "tags": sorted(set(args.tags)),
        "done": False,
        "created": datetime.now().isoformat(timespec="seconds"),
        "completed": None,
    }
    tasks.append(task)
    save(tasks)
    print(f"added task {task['id']}: {task['title']}")


def cmd_done(args):
    tasks = load()
    t, iid = get(tasks, args.id)
    t["done"] = True
    t["completed"] = datetime.now().isoformat(timespec="seconds")
    save(tasks)
    print(f"marked task {iid} done: {t['title']}")


def cmd_undo(args):
    tasks = load()
    t, iid = get(tasks, args.id)
    t["done"] = False
    t["completed"] = None
    save(tasks)
    print(f"reopened task {iid}: {t['title']}")


def cmd_rm(args):
    tasks = load()
    _, iid = get(tasks, args.id)
    tasks = [t for t in tasks if t["id"] != iid]
    save(tasks)
    print(f"deleted task {iid}")


def cmd_edit(args):
    tasks = load()
    t, iid = get(tasks, args.id)
    if args.title:
        t["title"] = args.title
    t["priority"] = args.priority or t["priority"]
    if args.due is not None:
        t["due"] = args.due or None
    if args.tags:
        new = set(t["tags"]) | set(args.tags)
        t["tags"] = sorted(new)
    save(tasks)
    print(f"updated task {iid}: {t['title']}")


def cmd_purge(args):
    tasks = load()
    n = sum(1 for t in tasks if t["done"])
    tasks = [t for t in tasks if not t["done"]]
    save(tasks)
    print(f"purged {n} completed task(s)")


def priority_rank(p):
    return {"high": 0, "medium": 1, "low": 2}[p]


def sort_key(t):
    # Open tasks first, then by due date (None sorts last), then priority, then id.
    return (t["done"], t["due"] or "9999-12-31", priority_rank(t["priority"]), t["id"])


def fmt_date(d):
    if not d:
        return "     "
    today = date.today()
    if d == today.isoformat():
        return "TODAY"
    if d < today.isoformat():
        return "OVERD"
    return d[5:]


def cmd_list(args):
    tasks = load()
    if args.done:
        tasks = [t for t in tasks if t["done"]]
    elif not args.all:
        tasks = [t for t in tasks if not t["done"]]
    if args.tag:
        tasks = [t for t in tasks if args.tag in t["tags"]]
    if args.status:
        tasks = [t for t in tasks if t["priority"] == args.status]
    tasks.sort(key=sort_key)

    if not tasks:
        print("(nothing to show)")
        return
    print(f"{'ID':<4} {'PRI':<6} {'DUE':<7} TAGS        TITLE")
    print("-" * 60)
    for t in tasks:
        tags = ",".join(t["tags"]) if t["tags"] else ""
        mark = "x" if t["done"] else " "
        print(f"{t['id']:<4} {t['priority']:<6} {fmt_date(t['due']):<7} "
              f"{tags:<11} {mark} {t['title']}")


def cmd_stats(args):
    tasks = load()
    open_n = sum(1 for t in tasks if not t["done"])
    done_n = sum(1 for t in tasks if t["done"])
    overdue = sum(1 for t in tasks
                  if not t["done"] and t["due"] and t["due"] < date.today().isoformat())
    by_pri = {p: sum(1 for t in tasks if not t["done"] and t["priority"] == p)
              for p in ("high", "medium", "low")}
    print(f"open      : {open_n}")
    print(f"completed : {done_n}")
    print(f"overdue   : {overdue}")
    print(f"open by priority: high={by_pri['high']} medium={by_pri['medium']} low={by_pri['low']}")


def build_parser():
    p = argparse.ArgumentParser(prog="todo", description="A minimal command-line task manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a new task")
    a.add_argument("title", nargs="?", help="task title")
    a.add_argument("-p", "--priority", choices=sorted(PRIORITIES), default="medium")
    a.add_argument("-d", "--due", help="due date YYYY-MM-DD")
    a.add_argument("-t", "--tag", dest="tags", action="append", default=[])
    a.set_defaults(func=cmd_add)

    sub.add_parser("done", help="mark a task done").add_argument("id")
    sub.add_parser("undo", help="reopen a task").add_argument("id")
    sub.add_parser("rm", help="delete a task").add_argument("id")
    sub.add_parser("purge", help="delete all completed tasks")
    sub.add_parser("stats", help="show summary counts")

    # Bind handlers that take only an id (or nothing).
    for name, fn in {"done": cmd_done, "undo": cmd_undo, "rm": cmd_rm,
                     "purge": cmd_purge, "stats": cmd_stats}.items():
        sub.choices[name].set_defaults(func=fn)

    e = sub.add_parser("edit", help="edit a task")
    e.add_argument("id")
    e.add_argument("title", nargs="?", help="new title")
    e.add_argument("-p", "--priority", choices=sorted(PRIORITIES))
    e.add_argument("-d", "--due", help="new due date YYYY-MM-DD (empty to clear)")
    e.add_argument("-t", "--tag", dest="tags", action="append", default=[])
    e.set_defaults(func=cmd_edit)

    l = sub.add_parser("list", help="list tasks")
    l.add_argument("--done", action="store_true", help="only completed tasks")
    l.add_argument("-t", "--tag", help="filter by tag")
    l.add_argument("-s", "--status", choices=sorted(PRIORITIES), help="filter by priority")
    l.add_argument("-a", "--all", action="store_true", help="include completed (default list excludes them)")
    l.set_defaults(func=cmd_list)

    for subp in (sub.choices["done"], sub.choices["undo"], sub.choices["rm"]):
        subp.set_defaults(func=globals()["cmd_" + subp.prog.split()[-1]])
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
