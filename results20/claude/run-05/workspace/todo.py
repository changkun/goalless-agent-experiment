#!/usr/bin/env python3
"""todo — a small, zero-dependency command-line todo manager.

Stores tasks as JSON in ~/.todo/tasks.json.

Usage:
  todo add <text> [--project NAME] [--priority p1|p2|p3]
  todo ls [--project NAME] [--all] [--done]
  todo done <id> ...
  todo undo <id> ...
  todo rm <id> ...
  todo projects
  todo help
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("TODO_DIR", Path.home() / ".todo"))
DATA_FILE = DATA_DIR / "tasks.json"

PRIORITIES = {"p1": 1, "p2": 2, "p3": 3}
PRI_LABEL = {1: "p1", 2: "p2", 3: "p3"}
PRI_MARK = {1: "\033[31m⚠\033[0m", 2: "\033[33m◐\033[0m", 3: "\033[36m○\033[0m"}


def _sep():
    return "─" * 60


class TodoList:
    def __init__(self, tasks=None):
        self.tasks = tasks if tasks is not None else []
        self._next_id = (max((t["id"] for t in self.tasks), default=0) + 1)

    # ---- persistence -------------------------------------------------------
    @classmethod
    def load(cls):
        if not DATA_FILE.exists():
            return cls()
        try:
            data = json.loads(DATA_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            print(f"[todo] warning: could not read {DATA_FILE}; starting fresh", file=sys.stderr)
            return cls()
        return cls(data.get("tasks", []))

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps({"tasks": self.tasks}, indent=2) + "\n")

    # ---- queries -----------------------------------------------------------
    def find(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        return None

    def visible(self, project=None, include_done=False, done_only=False):
        out = []
        for t in self.tasks:
            if done_only and not t["done"]:
                continue
            if t["done"] and not include_done:
                continue
            if project and t.get("project") != project:
                continue
            out.append(t)
        out.sort(key=lambda t: (t["done"], PRIORITIES[t.get("priority", "p3")], t["id"]))
        return out

    # ---- mutations ---------------------------------------------------------
    def add(self, text, project=None, priority="p3"):
        priority = priority if priority in PRIORITIES else "p3"
        task = {
            "id": self._next_id,
            "text": text,
            "project": project,
            "priority": priority,
            "done": False,
            "created": int(time.time()),
            "completed": None,
        }
        self.tasks.append(task)
        self._next_id += 1
        return task

    def set_done(self, task_id, done):
        t = self.find(task_id)
        if not t:
            return None
        t["done"] = done
        t["completed"] = int(time.time()) if done else None
        return t

    def remove(self, task_id):
        for i, t in enumerate(self.tasks):
            if t["id"] == task_id:
                return self.tasks.pop(i)
        return None


def _fmt(t, width=40):
    pri = PRI_MARK.get(PRIORITIES[t.get("priority", "p3")], "○")
    check = "\033[32m✓\033[0m" if t["done"] else "·"
    text = t["text"]
    if len(text) > width:
        text = text[: width - 1] + "…"
    project = f" \033[90m[{t['project']}]\033[0m" if t.get("project") else ""
    return f"{t['id']:>3} {check} {pri} {text}{project}"


def _project_summary(tlist):
    counts = {}
    for t in tlist.tasks:
        counts.setdefault(t.get("project") or "(none)", [0, 0])
        counts[t.get("project") or "(none)"][0] += 1
        if not t["done"]:
            counts[t.get("project") or "(none)"][1] += 1
    return counts


def cmd_add(args, tlist):
    if not args.text:
        print("[todo] add requires some text", file=sys.stderr)
        return 1
    t = tlist.add(" ".join(args.text), project=args.project, priority=args.priority)
    tlist.save()
    print(f"Added task {t['id']}: {t['text']}")
    return 0


def cmd_ls(args, tlist):
    items = tlist.visible(
        project=args.project,
        include_done=args.all or args.done,
        done_only=args.done and not args.all,
    )
    if not items:
        print("[todo] nothing to show.")
        return 0
    print(_sep())
    for t in items:
        print(_fmt(t))
    print(_sep())
    open_count = sum(1 for t in items if not t["done"])
    print(f"{open_count} open, {len(items) - open_count} done")
    return 0


def cmd_set(args, tlist, done):
    if not args.ids:
        print(f"[todo] provide at least one id", file=sys.stderr)
        return 1
    missing = [i for i in args.ids if not tlist.find(i)]
    if missing:
        print(f"[todo] no such id(s): {', '.join(map(str, missing))}", file=sys.stderr)
        return 1
    for i in args.ids:
        t = tlist.set_done(i, done)
        verb = ("Completed" if done else "Reopened") + f" task {t['id']}"
        print(f"{verb}: {t['text']}")
    tlist.save()
    return 0


def cmd_rm(args, tlist):
    if not args.ids:
        print("[todo] provide at least one id", file=sys.stderr)
        return 1
    for i in args.ids:
        t = tlist.remove(i)
        if not t:
            print(f"[todo] no such id: {i}", file=sys.stderr)
            continue
        print(f"Deleted task {t['id']}: {t['text']}")
    tlist.save()
    return 0


def cmd_projects(args, tlist):
    counts = _project_summary(tlist)
    if not counts:
        print("[todo] no projects yet.")
        return 0
    width = max(len(p) for p in counts)
    print(_sep())
    for name, (total, openc) in sorted(counts.items()):
        bar = "█" * openc + "░" * (total - openc)
        print(f"{name:<{width}}  {openc:>2}/{total:<2} {bar}")
    print(_sep())
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo", description="a small todo manager")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("text", nargs="*")
    p_add.add_argument("--project")
    p_add.add_argument("--priority", choices=sorted(PRIORITIES), default="p3")
    p_add.set_defaults(func=lambda a, t: cmd_add(a, t))

    p_ls = sub.add_parser("ls", help="list tasks")
    p_ls.add_argument("--project")
    p_ls.add_argument("--all", action="store_true", help="include done tasks")
    p_ls.add_argument("--done", action="store_true", help="show only done tasks")
    p_ls.set_defaults(func=lambda a, t: cmd_ls(a, t))

    for name, done in (("done", True), ("undo", False)):
        pd = sub.add_parser(name, help=f"{'mark done' if done else 'reopen'} tasks")
        pd.add_argument("ids", nargs="*", type=int)
        pd.set_defaults(func=lambda a, t, d=done: cmd_set(a, t, d))

    p_rm = sub.add_parser("rm", help="delete tasks")
    p_rm.add_argument("ids", nargs="*", type=int)
    p_rm.set_defaults(func=lambda a, t: cmd_rm(a, t))

    sub.add_parser("projects", help="task counts per project").set_defaults(
        func=lambda a, t: cmd_projects(a, t)
    )

    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0

    tlist = TodoList.load()
    return args.func(args, tlist)


if __name__ == "__main__":
    sys.exit(main())
