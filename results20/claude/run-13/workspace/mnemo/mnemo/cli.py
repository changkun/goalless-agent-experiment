"""Command-line interface for Mnemo.

Subcommands:
    add FRONT BACK   - add a card
    list             - list all cards
    due              - show cards due today
    review           - interactive review session for due cards
    stats            - deck statistics

The default database is ``~/.mnemo/deck.db``, overridable with ``--db``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .db import Deck, today
from .sm2 import QUALITY_EASY, QUALITY_GOOD, schedule

DEFAULT_DB = Path.home() / ".mnemo" / "deck.db"

# rating -> SM-2 quality
_RATINGS = {
    "0": 0,  # again / forgot
    "1": 3,  # hard
    "2": 4,  # good
    "3": 5,  # easy
}


def _deck(path: str | None) -> Deck:
    return Deck(Path(path) if path else DEFAULT_DB)


def _format_due(due: int) -> str:
    diff = due - today()
    if diff <= 0:
        return "due now"
    if diff == 1:
        return "in 1 day"
    return f"in {diff} days"


def cmd_add(deque: Deck, args) -> None:
    card_id = deque.add(args.front, args.back)
    print(f"Added card #{card_id}: {args.front}")


def cmd_list(deque: Deck, _args) -> None:
    cards = deque.all()
    if not cards:
        print("No cards yet. Try: mnemo add 'question' 'answer'")
        return
    for c in cards:
        print(f"[{c['id']:>3}] ease={c['ease']:.2f} "
              f"ivl={c['interval']:>3}d reps={c['reps']:>3} "
              f"{_format_due(c['due']):<10} "
              f"{c['front'][:40]!r}")
    print(f"\n{len(cards)} card(s) total.")


def cmd_due(deque: Deck, _args) -> None:
    cards = deque.due()
    for c in cards:
        print(f"[{c['id']:>3}] {c['front']!r} -> {c['back']!r}")
    print(f"\n{len(cards)} card(s) due.")


def cmd_stats(deque: Deck, _args) -> None:
    s = deque.stats()
    print(f"Total cards   : {s['total']}")
    print(f"Due today     : {s['due_count']}")
    print(f"Total lapses  : {s['total_lapses']}")
    print(f"Average ease  : {s['avg_ease']}")


def cmd_review(deque: Deck, args) -> None:
    cards = deque.due()
    if not cards:
        print("Nothing due right now. Add cards or come back later!")
        return
    print(f"{len(cards)} card(s) due. Enter rating after flipping each card.")
    print("Ratings: 0=again  1=hard  2=good  3=easy   (q=quit)\n")

    reviewed = 0
    for card in cards:
        if args.quiet:
            print(f"[{card['id']}] {card['front']!r}")
        else:
            input(f"[{card['id']}] {card['front']}\n"
                  f"    (press Enter to reveal answer)")
            print(f"    {card['back']}")

        while True:
            raw = input("    rating [0/1/2/3] > ").strip().lower()
            if raw in ("q", "quit", "exit"):
                print(f"\nStopped. {reviewed} card(s) reviewed.")
                return
            if raw in _RATINGS:
                quality = _RATINGS[raw]
                break
            print("    Invalid rating.")

        state = deque.card_state(card)
        new_state = schedule(state, quality, today())
        due = today() + new_state.interval
        deque.update_state(card["id"], new_state, due)
        reviewed += 1
        if quality == 0:
            print(f"    -> lapsed; next review in 1 day")
        else:
            print(f"    -> next review in {new_state.interval} day(s)")

    print(f"\nDone! Reviewed {reviewed} card(s).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mnemo",
        description="A minimal spaced-repetition flashcard CLI (SM-2).",
    )
    parser.add_argument("--version", action="version",
                        version=f"mnemo {__version__}")
    parser.add_argument("--db", default=None,
                        help=f"path to database (default: {DEFAULT_DB})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new card")
    p_add.add_argument("front", help="question / prompt")
    p_add.add_argument("back", help="answer")
    p_add.set_defaults(func=cmd_add)

    sub.add_parser("list", help="list all cards").set_defaults(func=cmd_list)
    sub.add_parser("due", help="show cards due").set_defaults(func=cmd_due)
    sub.add_parser("stats", help="deck statistics").set_defaults(func=cmd_stats)

    p_review = sub.add_parser("review", help="review due cards")
    p_review.add_argument("-q", "--quiet", action="store_true",
                          help="no flip prompt (for scripting/tests)")
    p_review.set_defaults(func=cmd_review)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    deque = _deck(args.db)
    try:
        args.func(deque, args)
    finally:
        deque.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
