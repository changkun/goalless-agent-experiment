"""Streak calculation helpers."""

from datetime import date, timedelta


def current_streak(dates, today=None):
    """Return the length of the consecutive run ending today (or the most
    recent checked day, if today wasn't checked yet)."""
    today = today or date.today()
    days = {_to_date(d) for d in dates}
    if not days:
        return 0
    cursor = today
    if cursor not in days:
        cursor -= timedelta(days=1)
    length = 0
    while cursor in days:
        length += 1
        cursor -= timedelta(days=1)
    return length


def longest_streak(dates):
    """Return the longest run of consecutive checked days."""
    days = sorted({_to_date(d) for d in dates})
    if not days:
        return 0
    best = 1
    run = 1
    for prev, cur in zip(days, days[1:]):
        if (cur - prev).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best


def _to_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
