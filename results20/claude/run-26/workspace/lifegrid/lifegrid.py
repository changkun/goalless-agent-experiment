#!/usr/bin/env python3
"""lifegrid — your life in weeks, drawn in ANSI. No dependencies."""

import argparse
import datetime as dt
import math
import os
import sys

# ---------------------------------------------------------------------------
# Color / effect tokens (empty when not a TTY or when NO_COLOR is set)
# ---------------------------------------------------------------------------

def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


PAST_FG = 231   # bright white
PAST_BG = 24    # deep teal-700
FUT_LO  = 236   # dim slate
FUT_HI  = 240   # slightly brighter slate


_ENABLED = _supports_color()

def _c(spec):
    return "\x1b[" + spec + "m" if _ENABLED else ""

RESET = _c("0")

def paint_char(ch, *specs):
    if not _ENABLED:
        return ch
    return _c(";".join(specs)) + ch + RESET


# ---------------------------------------------------------------------------
# Time math
# ---------------------------------------------------------------------------

WEEK = dt.timedelta(weeks=1)


def weeks_from_birth(born, day):
    return int((day - born).days // 7)


def frac_from_birth(born, day):
    return (day - born).days / 7.0


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

def render_grid(born, lifespan, width, today):
    """Draw the whole life as a grid of week-cells, wrapped to `width` columns.

    Every cell is exactly one week, laid out left-to-right, top-to-bottom from
    birth. Year labels are placed at each Jan 1's cell using the same flat
    week-index, so they always sit directly above the week they mark.
    """
    total_weeks = math.ceil(lifespan * 52.1775)
    lived = frac_from_birth(born, today)
    today_idx = int((today - born).days // 7)
    cols = max(1, width)
    rows_n = math.ceil(total_weeks / cols)

    def style(idx):
        if idx == today_idx:
            return paint_char("█", f"38;5;16;48;5;214")  # today: inverse amber
        if idx < lived:
            return paint_char("█", f"38;5;{PAST_FG};48;5;{PAST_BG}")
        frac = max(0.0, min(1.0, idx / total_weeks))
        bright = FUT_LO + int((FUT_HI - FUT_LO) * (1 - frac))
        return paint_char("▓", f"38;5;{bright}")

    # label overlay: each digit of a year sits at its own cell's (row, col)
    overlay = [None] * total_weeks
    for y in range(born.year, born.year + math.ceil(lifespan)):
        idx = int((dt.date(y, 1, 1) - born).days // 7)
        if idx < 0:
            continue
        if idx >= total_weeks:
            break
        for k, ch in enumerate(str(y)):
            if idx + k < total_weeks and overlay[idx + k] is None:
                overlay[idx + k] = ch

    out = []
    for r in range(rows_n):
        lo, hi = r * cols, min(total_weeks, (r + 1) * cols)
        hdr = "".join(ch if ch else " " for ch in overlay[lo:hi]).rstrip()
        body = "".join(style(i) for i in range(lo, hi))
        if hdr.strip():
            out.append(hdr)
        out.append(body)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Ratio bar
# ---------------------------------------------------------------------------

def render_ratio(born, lifespan, width, today):
    total_weeks = lifespan * 52.1775
    lived = weeks_from_birth(born, today)
    frac = lived / total_weeks
    n = max(1, width - 2)
    past = int(round(frac * n))
    seg = ""
    for i in range(n):
        if i < past:
            seg += paint_char("█", f"38;5;{PAST_FG};48;5;{PAST_BG}")
        else:
            seg += paint_char("░", f"38;5;{FUT_LO}")
    pct = frac * 100
    bar = f"[{seg}]"
    pad = " " * max(0, (width - len(bar)) // 2)
    label = f"lived {pct:.1f}% · ~{lived:,.0f} of {total_weeks:,.0f} weeks"
    return f"{pad}{bar}\n{pad}{label}"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def render_stats(born, lifespan, today):
    total_years = lifespan
    lived_years = (today - born).days / 365.2425
    remain_years = max(0.0, total_years - lived_years)

    lived_wk = weeks_from_birth(born, today)
    total_wk = math.ceil(total_years * 52.1775)
    remain_wk = max(0, total_wk - lived_wk)

    end = born + dt.timedelta(days=math.ceil(total_years * 365.2425))

    def age_at(frac):
        d = born + dt.timedelta(days=frac * total_years * 365.2425)
        return d, (d - today).days

    lines = []
    lines.append(paint_char("▍", "38;5;24") + " " + paint_char("lived", "1") +
                 f"\n   {lived_years:6.1f} years · {lived_wk:>7,d} weeks · "
                 f"{lived_years*12:>7,.0f} months")
    lines.append(paint_char("▍", "38;5;240") + " " + paint_char("remaining (at {:.0f})".format(total_years), "1") +
                 f"\n   {remain_years:6.1f} years · {remain_wk:>7,d} weeks · "
                 f"{remain_years*12:>7,.0f} months")
    lines.append("")
    # milestones
    for frac, name in [(0.25, "quarter-life"), (0.5, "mid-life"),
                       (0.75, "three-quarter"), (1.0, "end")]:
        d, days = age_at(frac)
        when = "today" if abs(days) < 3 else (
            f"in {days:,} days ({d:%b %Y})" if days > 0 else f"{abs(days):,} days ago ({d:%b %Y})")
        done = "◉" if days <= 0 else "○"
        lines.append(f" {done} {name:<15} {when}")
    lines.append(f"\n   weeks run out: {end:%b %d, %Y}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def terminal_width():
    try:
        return os.get_terminal_size().columns or 80
    except OSError:
        return 80


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lifegrid",
        description="Your life in weeks, drawn in your terminal. No deps.",
    )
    ap.add_argument("--born", required=True,
                    help="birth date, ISO YYYY-MM-DD")
    ap.add_argument("--lifespan", type=float, default=90.0,
                    help="assumed total years you'll live (default 90)")
    ap.add_argument("--view", default="grid", choices=["grid", "ratio", "stats"],
                    help="which visualization (default grid)")
    ap.add_argument("--width", type=int, default=None,
                    help="output width in columns (default: terminal width)")
    ap.add_argument("--today", default=None,
                    help="override 'today' for testing; ISO date")
    args = ap.parse_args(argv)

    born = dt.date.fromisoformat(args.born)
    today = (dt.date.fromisoformat(args.today)
             if args.today else dt.date.today())
    width = args.width or terminal_width()

    if args.lifespan <= 0:
        ap.error("--lifespan must be positive")

    if args.view == "stats":
        print(render_stats(born, args.lifespan, today))
    elif args.view == "ratio":
        print(render_ratio(born, args.lifespan, width, today))
    else:
        print(render_grid(born, args.lifespan, width, today))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
