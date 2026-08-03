"""Command-line interface for the spaced-repetition flashcard app."""

from __future__ import annotations

import argparse
import sys

from .scheduler import Deck


def cmd_add(deck: Deck, args: argparse.Namespace) -> int:
    card = deck.add(args.front, args.back)
    deck.save()
    print(f"Added card #{len(deck.cards)}: {card.front!r}")
    return 0


def cmd_list(deck: Deck, args: argparse.Namespace) -> int:
    if not deck.cards:
        print("No cards yet. Add some with 'srsflash add'.")
        return 0
    for i, card in enumerate(deck.cards, start=1):
        due_marker = "" if card.is_due() else " (not due)"
        print(f"{i}. [{card.front}] -> {card.back}{due_marker}")
    return 0


def cmd_review(deck: Deck, args: argparse.Namespace) -> int:
    due = deck.due_cards()
    if not due:
        print("Nothing due right now. Great job!")
        return 0
    print(f"{len(due)} card(s) due. Grade yourself 0-5 (3+ = recall success).\n")
    for card in due:
        print(f"--- {card.front} ---")
        input("Press Enter to reveal the answer...")
        print(f"Answer: {card.back}")
        while True:
            raw = input("Grade [0-5]: ").strip()
            if raw.isdigit() and 0 <= int(raw) <= 5:
                break
            print("Please enter a number between 0 and 5.")
        card.review(int(raw))
    deck.save()
    print("\nSession complete. Progress saved.")
    return 0


def cmd_remove(deck: Deck, args: argparse.Namespace) -> int:
    if not 1 <= args.index <= len(deck.cards):
        print(f"Invalid index. Must be between 1 and {len(deck.cards)}.", file=sys.stderr)
        return 1
    card = deck.remove(args.index - 1)
    deck.save()
    print(f"Removed card {args.index}: {card.front!r}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srsflash", description="Flashcards with spaced repetition.")
    parser.add_argument("--deck", default="deck.json", help="Path to deck file (default: deck.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new flashcard")
    p_add.add_argument("front", help="Question / front text")
    p_add.add_argument("back", help="Answer / back text")

    sub.add_parser("list", help="List all cards")

    p_rm = sub.add_parser("remove", help="Remove a card by index")
    p_rm.add_argument("index", type=int, help="1-based card index")

    sub.add_parser("review", help="Review due cards")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    deck = Deck(args.deck)

    handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "review": cmd_review,
        "remove": cmd_remove,
    }
    return handlers[args.command](deck, args)


if __name__ == "__main__":
    raise SystemExit(main())
