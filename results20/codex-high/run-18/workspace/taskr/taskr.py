#!/usr/bin/env python3
"""taskr - a tiny, dependency-free command-line task tracker.

Tasks are stored as JSON in a file (default: ~/.taskr.json).
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


DEFAULT_FILE = os.path.join(os.path.expanduser("~"), ".taskr.json")
STATUSES = ("todo", "in_progress", "done")


def load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if not content.strip():
        return []
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a valid task list")
    return data


def save(path: str, tasks: list) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def find_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def cmd_add(args, tasks):
    tasks.append(
        {
            "id": str(uuid.uuid4())[:8],
            "description": " ".join(args.description),
            "status": "todo",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    )
    return tasks


def cmd_list(args, tasks):
    if args.status and args.status not in STATUSES:
        raise ValueError(f"invalid status: {args.status}")
    filtered = [t for t in tasks if (not args.status or t["status"] == args.status)]
    if not filtered:
        print("No tasks.")
        return tasks
    width = max(len(t["description"]) for t in filtered)
    header = f"{'ID':8}  {'STATUS':<11}  {'DESCRIPTION':<{width}}"
    print(header)
    print("-" * len(header))
    for t in filtered:
        print(f"{t['id']:8}  {t['status']:<11}  {t['description']}")
    return tasks


def cmd_update(args, tasks):
    task = find_task(tasks, args.id)
    if task is None:
        raise ValueError(f"no task with id {args.id}")
    if args.status and args.status not in STATUSES:
        raise ValueError(f"invalid status: {args.status}")
    if args.status:
        task["status"] = args.status
    if args.description:
        task["description"] = " ".join(args.description)
    task["updated_at"] = now_iso()
    print(f"Updated task {args.id}.")
    return tasks


def cmd_delete(args, tasks):
    task = find_task(tasks, args.id)
    if task is None:
        raise ValueError(f"no task with id {args.id}")
    tasks = [t for t in tasks if t["id"] != args.id]
    print(f"Deleted task {args.id}.")
    return tasks


def build_parser():
    parser = argparse.ArgumentParser(prog="taskr", description="Tiny CLI task tracker.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="path to task file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("description", nargs="+")

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--status", choices=STATUSES, help="filter by status")

    p_update = sub.add_parser("update", help="mark a task done or change status")
    p_update.add_argument("id")
    p_update.add_argument("--status", choices=STATUSES, default="done")
    p_update.add_argument("--description", nargs="+")

    p_delete = sub.add_parser("delete", help="delete a task")
    p_delete.add_argument("id")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        tasks = load(args.file)
        tasks = {
            "add": cmd_add,
            "list": cmd_list,
            "update": cmd_update,
            "delete": cmd_delete,
        }[args.command](args, tasks)
        save(args.file, tasks)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
