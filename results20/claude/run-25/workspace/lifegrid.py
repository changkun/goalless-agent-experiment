#!/usr/bin/env python3
"""
lifegrid — your life as a grid of weeks.

One dot per week of your life. Columns are weeks of a year, rows are years.
Given a birthdate (or just a "remaining years" target), draw the weeks you've
already lived in one color and the weeks left in another, so you can see,
at a glance, how much of the box is filled.

Pure stdlib, no dependencies. Written to be a pleasant thing to have in
your dotfiles.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

# ── terminal color helpers ────────────────────────────────────────────────
# Use 256-color TrueColor-ish escapes when on a TTY; fall back to plain when
# piped (so `lifegrid | less` and file redirection aren't full of escape junk).


def _supports_color() -> bool:
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        return True  # modern Windows terminals handle ANSI
    return True


# A warm, muted palette that reads well on both light and dark backgrounds.
LIVED = "\033[38;5;203m"      # soft coral/red
REMAINING = "\033[38;5;240m"  # neutral grey
TODAY = "\033[38;5;220m"      # amber
RESET = "\033[0m"

WEEKS_PER_YEAR = 52


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="lifegrid",
        description="Draw your life as a grid of weeks.",
    )
    parser.add_argument(
        "--born", "-b",
        metavar="YYYY-MM-DD",
        help="Your date of birth. One of --born or --age is required.",
    )
    parser.add_argument(
        "--age", "-a",
        type=float,
        help="Your current age in years (e.g. 31.4).",
    )
    parser.add_argument(
        "--until", "-u",
        type=int,
        default=90,
        help="Draw the grid up to this age (default 90).",
    )
    parser.add_argument(
        "--weeks", "-w",
        type=int,
        help="Grid width in weeks overrides weeks-per-year (default 52).",
    )
    args = parser.parse_args()

    if args.born:
        born = dt.date.fromisoformat(args.born)
        age_weeks = max(0, (dt.date.today() - born).days // 7)
    elif args.age is not None:
        if args.age < 0:
            parser.error("--age must not be negative.")
        born = None
        age_weeks = int(args.age * WEEKS_PER_YEAR + 0.5)
    else:
        parser.error("Provide either --born YYYY-MM-DD or --age N (years).")

    total_weeks = args.until * WEEKS_PER_YEAR
    age_weeks = min(age_weeks, total_weeks)

    # If we know the birthdate, mark the week the *current* week sits in so
    # the "today" dot lands on the right spot in its year row.
    today_week = None
    if born is not None:
        today_week = (dt.date.today() - born).days // 7
        today_week = min(today_week, total_weeks)

    draw_grid(age_weeks, today_week, total_weeks, args.weeks or WEEKS_PER_YEAR)

    weeks_left = total_weeks - age_weeks
    pct = 100.0 * age_weeks / total_weeks if total_weeks else 0.0
    print_lived_line(age_weeks, weeks_left, pct, total_weeks)
    return 0


def draw_grid(age_weeks: int, today_week: int | None, total_weeks: int, width: int) -> None:
    """Print the grid, one dot per week. Rows are years, columns are weeks."""
    if not _supports_color():
        # Plain mode: lived = '#' , today = 'T', remaining = '.'
        for start in range(0, total_weeks, width):
            row = []
            for w in range(start, min(start + width, total_weeks)):
                if w == today_week:
                    row.append("T")
                elif w < age_weeks:
                    row.append("#")
                else:
                    row.append(".")
            print("".join(row))
        return

    for start in range(0, total_weeks, width):
        out = []
        for w in range(start, min(start + width, total_weeks)):
            if w == today_week:
                out.append(TODAY + "●" + RESET)
            elif w < age_weeks:
                out.append(LIVED + "●" + RESET)
            else:
                out.append(REMAINING + "●" + RESET)
        print("".join(out))


def print_lived_line(age_weeks: int, weeks_left: int, pct: float, total_weeks: int) -> None:
    years = age_weeks / WEEKS_PER_YEAR
    print()
    if not _supports_color():
        print(f"{years:.1f} years lived · {weeks_left:,} weeks left "
              f"(to age {total_weeks // WEEKS_PER_YEAR}) · {pct:.1f}% of the grid filled")
        return
    print(f"{LIVED}●{RESET} lived  "
          f"{TODAY}●{RESET} today  "
          f"{REMAINING}●{RESET} to go")
    print(f"{years:.1f} years lived · {weeks_left:,} weeks left "
          f"(to age {total_weeks // WEEKS_PER_YEAR}) · {pct:.1f}% of the grid filled")


if __name__ == "__main__":
    raise SystemExit(main())
