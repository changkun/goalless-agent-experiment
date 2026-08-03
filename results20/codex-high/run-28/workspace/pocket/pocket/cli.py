"""Command-line interface for Pocket."""

from __future__ import annotations

import argparse
import sys

from . import core


def _format(note: core.Note) -> str:
    tag = "[x]" if getattr(note, "done", False) else ("[ ]" if note.task else "   ")
    return f"{tag} {note.date}  {note.text}"


def cmd_add(args: argparse.Namespace) -> int:
    note = core.add(args.file, " ".join(args.text).strip(), task=args.as_task,
                    done=args.done)
    print(f"added {note.date}: {note.text}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    kind = "tasks" if args.tasks else ("notes" if args.notes else "all")
    items = core.list_items(args.file, kind=kind, days=args.days, limit=args.limit)
    if not items:
        print("nothing to show")
        return 0
    for note in items:
        print(_format(note))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    note = core.set_done(args.file, args.index, done=not args.undo)
    if note is None:
        print(f"error: no item at index {args.index}", file=sys.stderr)
        return 1
    state = "done" if (not args.undo) else "open"
    print(f"marked {state}: {note.text}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    note = core.remove(args.file, args.index)
    if note is None:
        print(f"error: no item at index {args.index}", file=sys.stderr)
        return 1
    print(f"removed: {note.text}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            sys.stdout.write(fh.read())
    except FileNotFoundError:
        print("journal is empty; add something first", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pocket",
        description="Capture notes and tasks into a single Markdown journal.",
    )
    parser.add_argument("--file", default=core.default_path(),
                        help=f"journal path (default: {core.default_path()})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a note or task")
    p_add.add_argument("--task", action="store_true", dest="as_task",
                       help="add as a task")
    p_add.add_argument("--done", action="store_true",
                       help="add a task that is already done")
    p_add.add_argument("text", nargs="+", help="text to add")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list items")
    g = p_list.add_mutually_exclusive_group()
    g.add_argument("--tasks", action="store_true", help="tasks only")
    g.add_argument("--notes", action="store_true", help="notes only")
    p_list.add_argument("--days", type=int, default=None,
                        help="only items from the last N days")
    p_list.add_argument("-n", "--limit", type=int, default=None,
                        help="show at most N items")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="mark an item done/open by index")
    p_done.add_argument("--undo", action="store_true", help="mark as open instead")
    p_done.add_argument("index", type=int, help="0-based index from `list`")
    p_done.set_defaults(func=cmd_done)

    p_rm = sub.add_parser("remove", help="remove an item by index")
    p_rm.add_argument("index", type=int, help="0-based index from `list`")
    p_rm.set_defaults(func=cmd_remove)

    p_show = sub.add_parser("show", help="print the raw journal file")
    p_show.set_defaults(func=cmd_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
