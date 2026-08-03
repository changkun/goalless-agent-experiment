#!/usr/bin/env python3
"""
todo.py — a tiny, dependency-free task manager.

Stores tasks in a JSON file in the current directory. No third-party
dependencies; pure Python stdlib. Run `todo.py --help` to see usage.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

STORE = os.environ.get("TODO_STORE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json"))

ANSI_RESET = "\033[0m"


def _code(num: int) -> str:
    return f"\033[{num}m"


# Terminals that don't support color: allow opting out.
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def paint(text: str, code: int, bold: bool = False) -> str:
    if not _USE_COLOR:
        return text
    b = _code(1) if bold else ""
    return f"{b}{_code(code)}{text}{ANSI_RESET}"


# ---- persistence ---------------------------------------------------------


def load_tasks() -> list[dict]:
    if not os.path.exists(STORE):
        return []
    try:
        with open(STORE, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"todo: could not read {STORE}: {exc}", file=sys.stderr)
        return []


def save_tasks(tasks: list[dict]) -> None:
    with open(STORE, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2, ensure_ascii=False)


def _next_id(tasks: list[dict]) -> int:
    return max((t["id"] for t in tasks), default=0) + 1


# ---- helpers -------------------------------------------------------------


def _due_str(due: str | None) -> str:
    if due is None:
        return paint("no due date", 90)
    try:
        target = date.fromisoformat(due)
    except ValueError:
        return paint(f"(bad date {due})", 90)
    if target == date.today():
        return paint("today", 33)
    delta = (target - date.today()).days
    if delta < 0:
        return paint(f"{abs(delta)}d overdue", 31)
    if delta == 0:
        return paint("today", 33)
    if delta == 1:
        return paint("tomorrow", 36)
    if delta <= 7:
        return paint(f"{delta}d", 36)
    return paint(target.isoformat(), 90)


def _priority_str(prio: str) -> str:
    codes = {"high": 31, "med": 33, "low": 90}
    return paint(prio.upper(), codes.get(prio, 37), bold=prio == "high")


def _parse_args(args: str) -> dict:
    """Turn free-form CLI args into task fields. E.g.: add buy milk --due fri --p high"""
    fields = {"tags": []}
    i = 0
    while i < len(args):
        if args[i] in ("--due", "-d") and i + 1 < len(args):
            fields["due"] = args[i + 1]
            i += 2
        elif args[i] in ("--p", "--prio", "-p") and i + 1 < len(args):
            fields["priority"] = args[i + 1]
            i += 2
        elif args[i] in ("--tag", "-t") and i + 1 < len(args):
            fields["tags"].append(args[i + 1])
            i += 2
        else:
            fields.setdefault("title", []).append(args[i])
            i += 1
    if "title" in fields:
        fields["title"] = " ".join(fields["title"])
    return fields


def _resolve_date(when: str) -> str | None:
    """Accept 'today'/'tomorrow'/'+3'/ISO dates for --due."""
    when = when.lower()
    if when == "today":
        return date.today().isoformat()
    if when == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    if when.startswith("+") and when[1:].isdigit():
        return (date.today() + timedelta(days=int(when[1:]))).isoformat()
    try:
        date.fromisoformat(when)
        return when
    except ValueError:
        return None


def _find(tasks: list[dict], ref: str) -> dict | None:
    """Match by numeric id, or by a unique substring of the title."""
    if ref.isdigit():
        return next((t for t in tasks if t["id"] == int(ref)), None)
    matches = [t for t in tasks if ref.lower() in t["title"].lower()]
    if len(matches) == 1:
        return matches[0]
    return None


# ---- commands ------------------------------------------------------------


def cmd_add(tasks: list[dict], fields: dict) -> None:
    title = fields.get("title", "").strip()
    if not title:
        print("todo: give the task a title, e.g.  todo add 'write report'", file=sys.stderr)
        sys.exit(1)
    task = {
        "id": _next_id(tasks),
        "title": title,
        "done": False,
        "priority": fields.get("priority", "med"),
        "due": None,
        "tags": fields.get("tags", []),
        "created": datetime.now().isoformat(timespec="minutes"),
    }
    if fields.get("due"):
        resolved = _resolve_date(fields["due"])
        if resolved is None:
            print(f"todo: could not parse due date {fields['due']!r}", file=sys.stderr)
            sys.exit(1)
        task["due"] = resolved
    tasks.append(task)
    save_tasks(tasks)
    print(f"added {paint(f'#{task['id']}', 36)} {title}")


def cmd_done(tasks: list[dict], refs: list[str]) -> None:
    changed = 0
    for ref in refs:
        t = _find(tasks, ref)
        if t is None:
            print(f"todo: no task matches {ref!r}", file=sys.stderr)
            continue
        t["done"] = True
        changed += 1
    if changed:
        save_tasks(tasks)
    print(f"completed {paint(str(changed), 32)} task(s)")


def cmd_rm(tasks: list[dict], refs: list[str]) -> None:
    targets = [t for r in refs if (t := _find(tasks, r)) is not None]
    missing = len(refs) - len(targets)
    for t in targets:
        tasks.remove(t)
    save_tasks(tasks)
    print(f"removed {paint(str(len(targets)), 31)} task(s){'  (%d not found)' % missing if missing else ''}")


def cmd_list(tasks: list[dict], done: bool = False, tag: str | None = None) -> None:
    shown = [t for t in tasks if t["done"] == done]
    if tag:
        shown = [t for t in shown if tag in t["tags"]]
    if not shown:
        print(paint("  (nothing here)", 90))
        return

    # Sort: open by priority then due; done by completion signal (keep insertion).
    if not done:
        rank = {"high": 0, "med": 1, "low": 2}
        shown.sort(key=lambda t: (rank.get(t["priority"], 1), t["due"] or "9999"))

    for t in shown:
        _print_task(t)
    print(paint(f"\n  {len(shown)} open · {len(tasks) - len(shown)} done", 90))


def _print_task(t: dict) -> None:
    box = paint("✔" if t["done"] else " ", 32)
    prio = _priority_str(t.get("priority", "med"))
    due = _due_str(t.get("due"))
    tags = "".join(paint(f"  #{x}", 90) for x in t.get("tags", []))
    title = t["title"].rstrip(".")
    if t["done"]:
        title = paint(title, 90)
    line = f"  {box} {paint(f'#{t['id']:<3}', 36)}{title}"
    print(line)
    if prio != "MED" or due != "no due date" or tags:
        print(f"       {prio:>6}  {due}{tags}")


def cmd_stats(tasks: list[dict]) -> None:
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    open_tasks = total - done
    overdue = sum(1 for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < date.today())
    print(f"  {paint(str(open_tasks), 33)} open   {paint(str(done), 32)} done   {paint(str(overdue), 31)} overdue   of {total} total")
    if open_tasks:
        pct = int(100 * done / total)
        width = 24
        filled = int(width * done / total)
        bar = "█" * filled + "░" * (width - filled)
        print(f"   {bar} {paint(f'{pct}%', 90)}")
    else:
        print(paint("   all done — nice work.", 32))


# ---- main -----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="todo",
        description="A tiny, dependency-free task manager.",
        epilog="Examples:\n"
        "  todo add 'buy milk' --due tomorrow --p high --tag errands\n"
        "  todo                       # list open tasks\n"
        "  todo --done                # list completed tasks\n"
        "  todo do 3                  # mark task #3 done\n"
        "  todo search milk           # like list, but filtered",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    sub.add_parser("do", help="mark task(s) done").add_argument("ref", nargs="+")
    sub.add_parser("rm", help="remove task(s)").add_argument("ref", nargs="+")
    sub.add_parser("stats", help="show a summary")

    l = sub.add_parser("list", help="list tasks")
    l.add_argument("--done", action="store_true", help="show completed instead")
    l.add_argument("--tag", metavar="T", help="filter by tag")

    s = sub.add_parser("search", help="filter open tasks by substring")
    s.add_argument("term")

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    # 'add' accepts arbitrary flags after the title; parse them ourselves so
    # argparse doesn't reject --due/--p/--tag as unknown options.
    if argv and argv[0] == "add":
        tasks = load_tasks()
        cmd_add(tasks, _parse_args(argv[1:]))
        return 0

    args = build_parser().parse_args(argv)

    # bare call "todo" => list + stats
    if args.cmd is None:
        tasks = load_tasks()
        cmd_list(tasks)
        cmd_stats(tasks)
        return 0

    tasks = load_tasks()

    if args.cmd == "do":
        cmd_done(tasks, args.ref)
    elif args.cmd == "rm":
        cmd_rm(tasks, args.ref)
    elif args.cmd == "stats":
        cmd_stats(tasks)
    elif args.cmd == "list":
        cmd_list(tasks, done=args.done, tag=args.tag)
    elif args.cmd == "search":
        matched = [t for t in tasks if not t["done"] and args.term.lower() in t["title"].lower()]
        if not matched:
            print(paint(f"  no open tasks match {args.term!r}", 90))
        else:
            for t in matched:
                _print_task(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
