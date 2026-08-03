#!/usr/bin/env python3
"""td — a tiny, zero-dependency terminal task manager.

Tasks are stored as a simple JSON file (default ~/.config/td/tasks.json).
Each task:
    id          stable integer id
    text        the task description
    prio        0 (low) / 1 (normal) / 2 (high)
    done        bool
    tags        list of tags
    due         optional ISO date string (YYYY-MM-DD)
    created     ISO timestamp
    done_at     ISO timestamp or None

Commands:
    td                      list tasks
    td add TEXT [#tag...]   add a task  (aliases: a, new)
        --prio/-p 0|1|2     priority (default 1)
        --due/-d DATE       due date
    td done ID [ID...]      mark done (aliases: d, complete)
    td open ID [ID...]      mark not done (aliases: o)
    td rm ID [ID...]        delete permanently (aliases: del, delete)
    td edit ID TEXT         replace text
    td tag ID TAG [TAG...]  add tags
    td untag ID TAG[...]    remove tags
    td prio ID P            set priority
    td due ID DATE|none     set / clear due date
    td ls [FILTER...]       filter: [+tag] [-tag] [prio:P] [done|open] [today|overdue]
    td stats                show summary
    td clear-done           remove all completed tasks
    td help                 this help
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

CONFIG_DIR = os.environ.get("TD_DIR", os.path.expanduser("~/.config/td"))
DATA_FILE = os.path.join(CONFIG_DIR, "tasks.json")

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
GREY = "\033[90m"

PRIO_COLORS = {0: GREY, 1: CYAN, 2: RED}
PRIO_LABELS = {0: "low", 1: "norm", 2: "high"}


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE) as fh:
        return json.load(fh)


def save(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, DATA_FILE)


def by_id(data, iid):
    for t in data["tasks"]:
        if t["id"] == iid:
            return t
    return None


def normalize_date(s):
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        sys.exit(f"error: '{s}' is not a valid date (use YYYY-MM-DD)")


def cmd_add(data, args):
    words = []
    tags = []
    prio = 1
    due = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-p", "--prio") and i + 1 < len(args):
            prio = int(args[i + 1])
            i += 2
        elif a in ("-d", "--due") and i + 1 < len(args):
            due = normalize_date(args[i + 1])
            i += 2
        elif a.startswith("#"):
            tags.append(a[1:].lower())
            i += 1
        else:
            words.append(a)
            i += 1
    if not words:
        sys.exit("error: nothing to add (give a task description)")
    text = " ".join(words)
    t = {
        "id": data["next_id"],
        "text": text,
        "prio": prio if 0 <= prio <= 2 else 1,
        "done": False,
        "tags": sorted(set(tags)),
        "due": due,
        "created": datetime.now().isoformat(timespec="seconds"),
        "done_at": None,
    }
    data["tasks"].append(t)
    data["next_id"] += 1
    save(data)
    print(f"added [{t['id']}] {t['text']}")


def cmd_done(data, ids, state=True):
    for iid in ids:
        t = by_id(data, iid)
        if not t:
            print(f"warning: no task {iid}")
            continue
        t["done"] = state
        t["done_at"] = datetime.now().isoformat(timespec="seconds") if state else None
        print(f"{'done' if state else 'reopened'} [{t['id']}] {t['text']}")
    save(data)


def cmd_rm(data, ids):
    idset = set(ids)
    keep = [t for t in data["tasks"] if t["id"] not in idset]
    removed = len(data["tasks"]) - len(keep)
    data["tasks"] = keep
    save(data)
    print(f"removed {removed} task(s)")


def cmd_edit(data, iid, text):
    t = by_id(data, iid)
    if not t:
        sys.exit(f"error: no task {iid}")
    t["text"] = text
    save(data)


def cmd_tag(data, iid, tags, add=True):
    t = by_id(data, iid)
    if not t:
        sys.exit(f"error: no task {iid}")
    ts = set(t["tags"])
    if add:
        ts |= {x.lower() for x in tags}
    else:
        ts -= {x.lower() for x in tags}
    t["tags"] = sorted(ts)
    save(data)


def cmd_prio(data, iid, p):
    t = by_id(data, iid)
    if not t:
        sys.exit(f"error: no task {iid}")
    t["prio"] = p
    save(data)


def cmd_due(data, iid, d):
    t = by_id(data, iid)
    if not t:
        sys.exit(f"error: no task {iid}")
    t["due"] = normalize_date(d) if d != "none" else None
    save(data)


def filter_tasks(tasks, filters):
    result = tasks
    show_done = None
    for f in filters:
        if f.startswith("+"):
            tag = f[1:].lower()
            result = [t for t in result if tag in t["tags"]]
            show_done = show_done if show_done is not None else False
        elif f.startswith("-"):
            tag = f[1:].lower()
            result = [t for t in result if tag not in t["tags"]]
        elif f.startswith("prio:"):
            result = [t for t in result if t["prio"] == int(f[5:])]
        elif f == "done":
            result = [t for t in result if t["done"]]
        elif f == "open":
            result = [t for t in result if not t["done"]]
        elif f == "today":
            result = [t for t in result if t["due"] == date.today().isoformat()]
        elif f == "overdue":
            result = [t for t in result if t["due"] and t["due"] < date.today().isoformat() and not t["done"]]
        else:
            q = f.lower()
            result = [t for t in result if q in t["text"].lower()]
    return result


def fmt_task(t):
    today = date.today().isoformat()
    prio_mark = {"2": "!", "1": " ", "0": "·"}[str(t["prio"])]
    cb = "✓" if t["done"] else " "
    line = f"{t['id']:>4} [{cb}] {prio_mark} "
    color = GREY if t["done"] else PRIO_COLORS[t["prio"]]
    line += f"{color}{t['text']}{RESET}"
    if t["due"]:
        overdue = t["due"] < today and not t["done"]
        due_color = RED if overdue else (YELLOW if t["due"] == today else BLUE)
        line += f"  {due_color}(due {t['due']}{'  OVERDUE' if overdue else ''}){RESET}"
    if t["tags"]:
        line += "  " + " ".join(f"{MAGENTA}#{x}{RESET}" for x in t["tags"])
    return line


def cmd_list(data, filters):
    tasks = filter_tasks(data["tasks"], filters)
    show_done = "done" in filters or any(f.startswith("+") for f in filters)
    tasks = sorted(tasks, key=lambda t: (t["done"], -t["prio"], t["id"]))
    if not tasks:
        print("(nothing matches)")
        return
    for i, t in enumerate(tasks):
        if t["done"] and not show_done:
            continue
        print(fmt_task(t))
    open_n = sum(1 for t in tasks if not t["done"])
    print(f"\n{BOLD}{len(tasks)} task(s), {open_n} open{RESET}")


def cmd_stats(data):
    ts = data["tasks"]
    open_t = [t for t in ts if not t["done"]]
    high = sum(1 for t in open_t if t["prio"] == 2)
    due_today = sum(1 for t in open_t if t["due"] == date.today().isoformat())
    overdue = sum(1 for t in open_t if t["due"] and t["due"] < date.today().isoformat())
    print(f"total:     {len(ts)}")
    print(f"open:      {len(open_t)}  (high: {high})")
    print(f"done:      {len(ts) - len(open_t)}")
    print(f"due today: {due_today}")
    print(f"overdue:   {overdue}")
    tags = {}
    for t in ts:
        for tag in t["tags"]:
            tags[tag] = tags.get(tag, 0) + 1
    if tags:
        popular = sorted(tags.items(), key=lambda kv: -kv[1])[:8]
        print("tags:      " + ", ".join(f"#{k} ({v})" for k, v in popular))


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "ls"
    rest = args[1:]

    data = load()
    if cmd in ("ls", "list"):
        cmd_list(data, rest)
    elif cmd in ("add", "a", "new"):
        cmd_add(data, rest)
    elif cmd in ("done", "d", "complete"):
        cmd_done(data, [int(x) for x in rest], True)
    elif cmd in ("open", "o"):
        cmd_done(data, [int(x) for x in rest], False)
    elif cmd in ("rm", "del", "delete"):
        cmd_rm(data, [int(x) for x in rest])
    elif cmd == "edit":
        if len(rest) < 2:
            sys.exit("usage: td edit ID TEXT")
        cmd_edit(data, int(rest[0]), " ".join(rest[1:]))
    elif cmd == "tag":
        cmd_tag(data, int(rest[0]), rest[1:], True)
    elif cmd == "untag":
        cmd_tag(data, int(rest[0]), rest[1:], False)
    elif cmd == "prio":
        cmd_prio(data, int(rest[0]), int(rest[1]))
    elif cmd == "due":
        cmd_due(data, int(rest[0]), rest[1])
    elif cmd == "stats":
        cmd_stats(data)
    elif cmd == "clear-done":
        n = len([t for t in data["tasks"] if t["done"]])
        data["tasks"] = [t for t in data["tasks"] if not t["done"]]
        save(data)
        print(f"cleared {n} completed task(s)")
    elif cmd in ("help", "-h", "--help"):
        print(__doc__)
    else:
        sys.exit(f"error: unknown command '{cmd}' (try 'td help')")


if __name__ == "__main__":
    main()
