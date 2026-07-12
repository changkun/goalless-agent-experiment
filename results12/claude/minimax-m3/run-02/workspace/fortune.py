#!/usr/bin/env python3
"""
fortune.py — a tiny fortune cookie for your terminal.

Rolls a fortune, a lucky number, an omen, and renders the whole thing
inside a hand-drawn ASCII cookie. Re-run for another fortune.

Usage:
    python3 fortune.py            # one fortune
    python3 fortune.py --many 5   # five fortunes
    python3 fortune.py --seed 7   # reproducible (try seeds 1..10 for variety)
"""

import argparse
import random
import sys
import textwrap
import time

# --- the pantry -----------------------------------------------------------

FORTUNES = [
    "A small step today is a giant leap by Friday.",
    "The bug you cannot find is in the line you refuse to read.",
    "Soon, a person you barely know will compliment your keyboard.",
    "Your next great idea is hiding behind a question you have not asked.",
    "The best refactor is the one you delete.",
    "An umbrella is not as useful as it thinks it is.",
    "A cookie is just a circle that committed to something.",
    "Patience is a virtue, but so is `kill -9`.",
    "The cloud is just someone else's computer, and they are tired.",
    "You will debug a missing semicolon for at least 23 minutes.",
    "Today is a good day to write the comment your past self needed.",
    "The undo button is a love letter to future you.",
    "Whitespace is never whitespace to a tired pair of eyes.",
    "The cleanest code is the code you did not write.",
    "Your tests will pass on the second try, which is the real first try.",
    "A duck is watching. Be kind.",
]

LUCKY_NUMBERS = list(range(1, 99))  # everyone gets a turn

OMENS = [
    ("a sparrow", "+++"),
    ("a black cat crossing left-to-right", "~🐈~"),
    ("a shooting star (dim, but yours)", "*·.·*"),
    ("a coin on the sidewalk, face down", "()"),
    ("the number eleven, in a license plate", "11"),
    ("a single green leaf on the pavement", "🌱"),
    ("three seagulls in a perfect line", "~~~"),
    ("a quiet hallway", "· · ·"),
]

COOKIE_ART = [
    "        .--._.--.",
    "       (  o  o  )",
    "      (   --   )",
    "       `------'",
]

# --- the oven -------------------------------------------------------------

def make_paper() -> str:
    return random.choice(FORTUNES)

def roll_omen() -> tuple[str, str]:
    return random.choice(OMENS)

def roll_lucky() -> int:
    # 7 and 42 get a small weighting bump because tradition demands it
    pool = LUCKY_NUMBERS + [7] * 3 + [42] * 2
    return random.choice(pool)

def wrap_paper(fortune: str, width: int = 44) -> list[str]:
    return textwrap.wrap(fortune, width=width) or ["(the cookie is empty)"]

def render(fortune: str, lucky: int, omen_name: str, omen_glyph: str) -> str:
    lines = []
    width = 50
    border = "+" + "-" * (width - 2) + "+"

    # the cookie itself
    lines.append(COOKIE_ART[0].center(width))
    lines.append(COOKIE_ART[1].center(width))
    lines.append(COOKIE_ART[2].center(width))
    lines.append(COOKIE_ART[3].center(width))
    lines.append("")

    # the paper
    lines.append(border)
    inner = width - 4  # padding: "|  text                |"
    for ln in wrap_paper(fortune, width=inner):
        lines.append("|  " + ln.ljust(inner) + "  |")
    lines.append(border)
    lines.append("")

    # stats
    lines.append(f"  lucky number : {lucky}".ljust(width))
    lines.append(f"  today's omen : {omen_name}".ljust(width))
    lines.append(f"                {omen_glyph}".ljust(width))
    lines.append("")
    lines.append("  (crack open another with: python3 fortune.py)".center(width))
    return "\n".join(lines)

def main() -> int:
    p = argparse.ArgumentParser(description="A tiny terminal fortune cookie.")
    p.add_argument("--many", type=int, default=1, help="how many fortunes to crack")
    p.add_argument("--seed", type=int, default=None, help="seed for reproducible fortunes")
    p.add_argument("--pause", type=float, default=0.0,
                   help="seconds to pause between fortunes (use ~0.4 for drama)")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        # mix in a bit of entropy so repeated runs differ
        random.seed(time.time_ns() ^ random.getrandbits(64))

    for i in range(args.many):
        if i > 0:
            time.sleep(args.pause)
        # de-dupe against every fortune already shown this run
        seen = set()
        fortune = make_paper()
        for _ in range(20):  # bounded retries; collisions are vanishingly rare
            if fortune not in seen:
                break
            fortune = make_paper()
        lucky = roll_lucky()
        omen_name, omen_glyph = roll_omen()
        print(render(fortune, lucky, omen_name, omen_glyph))
        if i < args.many - 1:
            print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
