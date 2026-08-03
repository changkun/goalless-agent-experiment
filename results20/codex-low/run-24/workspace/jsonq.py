#!/usr/bin/env python3
"""jsonq - a small dependency-free JSON tool.

Reads JSON from a file or stdin and supports:
  * pretty-printing
  * extracting values by dot-path (foo.bar[2].baz)
  * running a simple equality filter on a path
"""
import argparse
import json
import sys
from pathlib import Path


class PathError(ValueError):
    pass


def parse_path(path):
    """Parse 'foo.bar[0].baz' into a list of int/str keys."""
    keys = []
    i = 0
    token = ""
    while i < len(path):
        c = path[i]
        if c == ".":
            if token:
                keys.append(token)
                token = ""
            i += 1
        elif c == "[":
            if token:
                keys.append(token)
                token = ""
            j = path.find("]", i)
            if j == -1:
                raise PathError(f"unterminated '[' in path: {path}")
            raw = path[i + 1 : j]
            if not raw.isdigit():
                raise PathError(f"invalid list index '{raw}' in path: {path}")
            keys.append(int(raw))
            i = j + 1
        else:
            token += c
            i += 1
    if token:
        keys.append(token)
    return keys


def resolve(data, path):
    """Look up a path and return the value, or raise PathError if missing."""
    for key in parse_path(path):
        try:
            data = data[key]
        except (KeyError, IndexError, TypeError):
            raise PathError(f"path not found: {path} (stopped at {key!r})")
    return data


def matches(data, path, expected):
    """Return True if the value at path equals the expected parsed JSON value."""
    try:
        return resolve(data, path) == expected
    except PathError:
        return False


def parse_expected(text):
    """Parse a value, falling back to treating it as a string."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def emit_values(seq):
    for item in seq:
        sys.stdout.write(json.dumps(item))
        sys.stdout.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jsonq",
        description="Query and format JSON from a file or stdin.",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("file", nargs="?", help="input JSON file (default: stdin)")
    parser.add_argument("-q", "--query", metavar="PATH",
                        help="print the value at dot-path PATH")
    parser.add_argument("-f", "--filter", metavar="PATH=EXPECT",
                        help="only output items where PATH equals EXPECT")
    parser.add_argument("-i", "--inspect", action="store_true",
                        help="when filtering, print the selected item (default: matching items)")
    parser.add_argument("--indent", type=int, default=2,
                        help="indent for pretty output (default: 2)")
    args = parser.parse_args(argv)

    if args.file and args.file != "-":
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            parser.error(f"cannot read {args.file}: {exc}")
    else:
        text = sys.stdin.read()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON: {exc}")

    if args.filter:
        path, _, expected_raw = args.filter.partition("=")
        if not path or not expected_raw:
            parser.error("-f/--filter must be formatted as PATH=EXPECT")
        expected = parse_expected(expected_raw)
        if isinstance(data, list):
            items = list(data)
        else:
            items = [data]
        matches_obj = [item for item in items if matches(item, path, expected)]

        if args.inspect:
            for item in items:
                if matches(item, path, expected):
                    try:
                        sys.stdout.write(json.dumps(resolve(item, path)) + "\n")
                    except PathError:
                        pass
        else:
            for item in matches_obj:
                sys.stdout.write(json.dumps(item) + "\n")
        return

    if args.query:
        try:
            emit_values([resolve(data, args.query)])
        except PathError as exc:
            parser.error(str(exc))
        return

    sys.stdout.write(json.dumps(data, indent=args.indent) + "\n")


if __name__ == "__main__":
    main()
