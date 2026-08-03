#!/usr/bin/env python3
"""todo.py — a small, dependency-free command-line task manager.

Features:
  - Tasks with title, project, priority, due date, and tags
  - Plain JSON storage at ~/.todo.json (or $TODO_FILE)
  - Filters: by project, tag, priority, status, and (over)due
  - Sort by priority/due/created
  - Zero third-party dependencies — pure standard library
"""
import argparse
import json
import os
import sys
import datetime as dt

TODO_FILE = os.environ.get("TODO_FILE", os.path.expanduser("~/.todo.json"))
PRIORITIES = {"high": 3, "medium": 2, "low": 1}


def load():
    if not os.path.exists(TODO_FILE):
        return {"next_id": 1, "tasks": []}
    try:
        with open(TODO_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: could not read {TODO_FILE}: {e}", file=sys.stderr)
        sys.exit(1)


def save(data):
    tmp = TODO_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, TODO_FILE)


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        print(f"error: '{s}' is not a valid date (use YYYY-MM-DD)", file=sys.stderr)
        sys.exit(1)


def id_index(data, task_id):
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            return i
    print(f"error: no task with id {task_id}", file=sys.stderr)
    sys.exit(1)


def build_predicate(args):
    """Return a predicate (task -> bool) built from filter flags."""
    def pred(t):
        if args.project and args.project.lower() not in t["project"].lower():
            return False
        if args.tag and args.tag.lower() not in [x.lower() for x in t["tags"]]:
            return False
        if args.priority and t["priority"] != args.priority:
            return False
        if args.status == "open" and t["done"]:
            return False
        if args.status == "done" and not t["done"]:
            return False
        if args.due_none and t["due"] is not None:
            return False
        if args.due and (not t["due"] or t["due"] > args.due):
            return False
        if args.overdue and not (t["due"] and t["due"] < dt.date.today().isoformat() and not t["done"]):
            return False
        return True
    return pred


def sort_key(args, t):
    created = t["created"] or "0000-00-00"
    due = t["due"] or "9999-12-31"
    prior = PRIORITIES[t["priority"]]
    if args.sort == "due":
        return (due, -prior, created)
    if args.sort == "created":
        return (created,)
    # default: priority, then due
    return (-prior, due, created)


def fmt_status(t):
    mark = "[x]" if t["done"] else "[ ]"
    if t["done"]:
        return f"[x] #{t['id']} \033[9m{t['title']}\033[0m"  # strikethrough
    return f"[ ] #{t['id']} {t['title']}"


def list_tasks(data, args):
    pred = build_predicate(args)
    tasks = [t for t in data["tasks"] if pred(t)]
    tasks.sort(key=lambda t: sort_key(args, t))

    if args.count:
        print(f"{len(tasks)} task(s)")
        return

    if not tasks:
        print("nothing matches.")
        return

    for t in tasks:
        print(fmt_status(t))
        bits = []
        if t["project"]:
            bits.append(f"project:{t['project']}")
        bits.append(f"prio:{t['priority']}")
        if t["due"]:
            if not t["done"] and t["due"] < dt.date.today().isoformat():
                bits.append(f"due:{t['due']} \033[91m(OVERDUE)\033[0m")
            else:
                bits.append(f"due:{t['due']}")
        if t["tags"]:
            bits.append("#" + " #".join(t["tags"]))
        if bits:
            print("    " + "  ".join(bits))
        if args.verbose:
            print(f"    created:{t['created']}")
    print(f"\n{len(tasks)} task(s)")


def add(data, title, project=None, priority="medium", due=None, tags=None):
    if priority not in PRIORITIES:
        print(f"error: priority must be one of {', '.join(PRIORITIES)}",
              file=sys.stderr)
        sys.exit(1)
    task = {
        "id": data["next_id"],
        "title": title,
        "project": project or "",
        "priority": priority,
        "due": parse_date(due).isoformat() if due else None,
        "tags": sorted(set(t for t in (tags or []) if t)) if tags else [],
        "done": False,
        "created": dt.date.today().isoformat(),
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    print(f"added #{task['id']}: {title}")
    return task


def build_parser():
    parser = argparse.ArgumentParser(
        prog="todo", description="A small dependency-free task manager.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("-p", "--project")
    p_add.add_argument("-P", "--priority", default="medium", choices=list(PRIORITIES))
    p_add.add_argument("-d", "--due", help="YYYY-MM-DD")
    p_add.add_argument("-t", "--tag", action="append", dest="tags", metavar="TAG")

    for cmd in ("list", "ls"):
        pl = sub.add_parser(cmd, help="list tasks")
        pl.add_argument("--project", "-p")
        pl.add_argument("--tag", "-t")
        pl.add_argument("--priority", choices=list(PRIORITIES))
        pl.add_argument("--status", choices=["open", "done"])
        pl.add_argument("--due", help="tasks due on/before YYYY-MM-DD")
        pl.add_argument("--overdue", action="store_true",
                        help="open tasks past their due date")
        pl.add_argument("--due-none", action="store_true",
                        help="tasks with no due date")
        pl.add_argument("--sort", choices=["priority", "due", "created"],
                        default="priority")
        pl.add_argument("--count", action="store_true")
        pl.add_argument("--verbose", "-v", action="store_true")

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)
    p_done.add_argument("-u", "--undo", action="store_true",
                        help="mark not done instead")

    p_rename = sub.add_parser("rename", help="rename a task")
    p_rename.add_argument("id", type=int)
    p_rename.add_argument("new_title", nargs="+")

    p_rm = sub.add_parser("rm", help="delete a task")
    p_rm.add_argument("id", type=int)

    p_clear = sub.add_parser("clear", help="delete all done tasks")
    p_clear.add_argument("--force", action="store_true",
                         help="skip the confirmation dry-run")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command in ("list", "ls"):
        list_tasks(load(), args)
        return

    data = load()

    if args.command == "add":
        add(data, " ".join(args.title), args.project, args.priority,
            args.due, args.tags)
    elif args.command == "done":
        i = id_index(data, args.id)
        data["tasks"][i]["done"] = not args.undo
        print(f"#{args.id} " + ("reopened" if args.undo else "done"))
    elif args.command == "rename":
        i = id_index(data, args.id)
        data["tasks"][i]["title"] = " ".join(args.new_title)
        print(f"#{args.id} renamed")
    elif args.command == "rm":
        i = id_index(data, args.id)
        removed = data["tasks"].pop(i)
        print(f"removed #{args.id}: {removed['title']}")
    elif args.command == "clear":
        done = [t for t in data["tasks"] if t["done"]]
        if not args.force:
            print(f"Would delete {len(done)} done task(s). "
                  f"Re-run with --force to confirm.")
            return 0
        data["tasks"] = [t for t in data["tasks"] if not t["done"]]
        print(f"cleared {len(done)} done task(s)")

    save(data)


if __name__ == "__main__":
    main()
