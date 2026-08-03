#!/usr/bin/env python3
"""scraps - a tiny zero-dependency note-taking CLI.

Notes are stored as JSON. The store lives at $SCRAPS_FILE or
~/.scraps.json by default.
"""
import argparse
import json
import os
import sys


def default_path():
    env = os.environ.get("SCRAPS_FILE")
    if env:
        return env
    return os.path.join(os.path.expanduser("~"), ".scraps.json")


class Store:
    def __init__(self, path):
        self.path = path

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            return []
        if not isinstance(data, list):
            raise ValueError(f"{self.path} is not a valid scraps store")
        return data

    def save(self, notes):
        parent = os.path.dirname(self.path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(notes, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, self.path)


def next_id(notes):
    return (max((n["id"] for n in notes), default=0)) + 1


def add(store, text):
    notes = store.load()
    entry = {"id": next_id(notes), "text": text}
    notes.append(entry)
    store.save(notes)
    return entry


def remove(store, note_id):
    notes = store.load()
    remaining = [n for n in notes if n["id"] != note_id]
    if len(remaining) == len(notes):
        return False
    store.save(remaining)
    return True


def search(notes, term):
    term_l = term.lower()
    return [n for n in notes if term_l in n["text"].lower()]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="scraps",
        description="A tiny note-taking CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="add a note")
    add_p.add_argument("text", help="note text")

    ls_p = sub.add_parser("list", aliases=["ls"], help="list notes")
    ls_p.add_argument("--search", metavar="TERM", help="filter by substring")

    rm_p = sub.add_parser("remove", aliases=["rm"], help="remove a note by id")
    rm_p.add_argument("id", type=int, help="note id")

    args = parser.parse_args(argv)
    store = Store(default_path())

    if args.command in ("add",):
        entry = add(store, args.text)
        print(f"added {entry['id']}: {entry['text']}")
        return 0

    if args.command in ("list", "ls"):
        notes = store.load()
        if args.search:
            notes = search(notes, args.search)
        for n in notes:
            print(f"{n['id']}\t{n['text']}")
        return 0

    if args.command in ("remove", "rm"):
        if remove(store, args.id):
            print(f"removed {args.id}")
        else:
            print(f"no note with id {args.id}", file=sys.stderr)
            return 1
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
