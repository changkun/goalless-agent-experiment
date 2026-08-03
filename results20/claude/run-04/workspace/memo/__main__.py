"""Command-line interface for memo.

Usage
-----
    python -m memo add      "Buy oat milk #errands #today"
    python -m memo search   #errands #today        (AND semantics)
    python -m memo search   --prefix work          (tag prefix match)
    python -m memo tags                            (frequent-first)
    python -m memo ls
    python -m memo rm 123
    python -m memo help
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import List

from .core import MemoError, MemoStore, seed_if_empty

DEFAULT_PATH = os.environ.get("MEMO_PATH", os.path.join(".", "memo.json"))


def _store() -> MemoStore:
    return MemoStore(DEFAULT_PATH)


def _fmt(m: object) -> str:
    import time as _time

    ts = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(m.ts))
    # Text already contains the inline #tags; strip them so they appear once.
    body = re.sub(r" *#\S+", "", m.text).strip()
    tags = "".join(f" #{t}" for t in m.tags)
    return f"[{m.id}] {ts}  {body}{tags}"


def cmd_add(args) -> int:
    store = _store()
    memo = store.add(" ".join(args.text))
    print(_fmt(memo))
    return 0


def cmd_search(args) -> int:
    store = _store()
    rows = store.search(args.tags, prefix=args.prefix)
    if not rows:
        print("(no matches)")
    for m in rows:
        print(_fmt(m))
    return 0


def cmd_ls(args) -> int:
    store = _store()
    rows = store.search()
    if not rows:
        print("(empty)")
    for m in rows:
        print(_fmt(m))
    return 0


def cmd_tags(args) -> int:
    for t in _store().tags():
        print(t)
    return 0


def cmd_rm(args) -> int:
    if not _store().delete(int(args.id)):
        print(f"no memo with id {args.id}")
        return 1
    print(f"removed {args.id}")
    return 0


def cmd_init(args) -> int:
    seed_if_empty(_store())
    print(f"store ready at {DEFAULT_PATH}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="memo", description="A tiny tagged journal.")
    sub = p.add_subparsers(dest="command")

    a = sub.add_parser("add", help="add a memo")
    a.add_argument("text", nargs="+")
    a.set_defaults(func=cmd_add)

    s = sub.add_parser("search", help="search by tags (AND)")
    s.add_argument("--prefix", action="store_true", help="prefix-match tags")
    s.add_argument("tags", nargs="*")
    s.set_defaults(func=cmd_search)

    sub.add_parser("ls", help="list all memos").set_defaults(func=cmd_ls)
    sub.add_parser("tags", help="list all tags").set_defaults(func=cmd_tags)

    r = sub.add_parser("rm", help="remove a memo by id")
    r.add_argument("id")
    r.set_defaults(func=cmd_rm)

    sub.add_parser("init", help="ensure the store exists").set_defaults(func=cmd_init)
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None or args.command == "help":
        build_parser().print_help()
        return 0
    try:
        return args.func(args)
    except MemoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
