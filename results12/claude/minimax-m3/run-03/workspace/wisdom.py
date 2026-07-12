#!/usr/bin/env python3
"""wisdom.py — a tiny terminal wisdom dispenser.

Pulls a fortune, a koan, and lucky numbers for the day.
Deterministic per (date, locale) so reruns match, no surprises.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import random
import sys
import textwrap
from pathlib import Path

BANNER = r"""
 _    _  ____  _____  _      ____  ___  _   _ _____  _      ____
 | |  | |/ _  || ____|| |    |  _ \|_ _|| \ | |_   _|| |    / ___|
 | |  | | |_| ||  _|  | |    | |_) || | |  \| | | |  | |    \___ \
 | |__| |  _  || |___ | |___ |  _ < | | | |\  | | |  | |___  ___) |
 |_____||_| |_||_____||_____||_| \_\|___||_| \_| |_|  |_____||____/
"""

FORTUNES = [
    "The obstacle you keep mentioning is the path.",
    "You will debug a bug by explaining it to a rubber duck.",
    "A small commit today is worth a heroic rebase tomorrow.",
    "The function you are afraid to write is the one you should write first.",
    "Your future self sends thanks for the test you are about to add.",
    "There is a typo you have not noticed yet. It does not matter.",
    "Soon you will meet a variable named `data` that is not data.",
    "The best refactor is the one you almost did not do.",
    "A regex you understand today will confuse you tomorrow.",
    "Wisdom is knowing that `git reflog` exists.",
]

KOANS = [
    "A program that runs is a program not yet read by anyone.",
    "The bug is not in the code; the bug is in your model of the code.",
    "When the test passes and you feel nothing, the test is wrong.",
    "The junior writes code that works. The senior writes code that fails clearly.",
    "Premature optimization is the root of all evil; so is premature abstraction.",
    "There are two hard things: cache invalidation, naming, and off-by-one errors.",
    "Silence is a perfectly valid log level.",
    "If it is not in version control, it did not happen.",
]

COLOPHONS = [
    "— whispered by the static",
    "— overheard in /var/log",
    "— scraped off the ribbon cable",
    "— translated from a stack trace",
    "— overheard at the kernel level",
    "— a fragment of stderr",
]


def _seeded_rng(date: dt.date, locale: str) -> random.Random:
    h = hashlib.sha256(f"{date.isoformat()}|{locale}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def render(date: dt.date, locale: str = "en") -> str:
    rng = _seeded_rng(date, locale)
    fortune = rng.choice(FORTUNES)
    koan = rng.choice(KOANS)
    colophon = rng.choice(COLOPHONS)
    numbers = sorted(rng.sample(range(1, 70), 6))
    bonus = rng.randint(1, 27)

    width = 64
    body = []
    body.append(BANNER.rstrip())
    body.append(f"  {date.strftime('%A, %B %-d, %Y')}")
    body.append("")
    body.append("  · fortune ·".center(width, "─"))
    body.append(_wrap(f"  {fortune}", width))
    body.append("")
    body.append("  · koan ·".center(width, "─"))
    body.append(_wrap(f"  {koan}", width))
    body.append(f"  {colophon}")
    body.append("")
    body.append("  · lucky numbers ·".center(width, "─"))
    body.append("  " + "  ".join(f"{n:>2}" for n in numbers) + f"   bonus: {bonus:>2}")
    body.append("")
    return "\n".join(body)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Terminal wisdom dispenser.")
    p.add_argument(
        "--date",
        help="ISO date (YYYY-MM-DD). Defaults to today.",
    )
    p.add_argument(
        "--locale",
        default="en",
        help="Locale tag (changes the seed so reruns match your tongue).",
    )
    p.add_argument(
        "--out",
        type=Path,
        help="Write to this file instead of stdout.",
    )
    args = p.parse_args(argv)

    if args.date:
        date = dt.date.fromisoformat(args.date)
    else:
        date = dt.date.today()

    rendered = render(date, args.locale)
    if args.out:
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        sys.stdout.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
