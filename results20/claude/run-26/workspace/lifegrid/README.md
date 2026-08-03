# lifegrid

A zero-dependency, terminal-only visualization of the time you have.

It renders the classic **"your life in weeks"** grid — every week of your life is
one cell, laid out left-to-right, top-to-bottom, with each year's label drawn
directly above the week it marks. Built entirely from ANSI escape codes. No
external packages, no HTML, no JavaScript. Just Python 3 and a terminal.

At a 30-column width it looks like this:

```
1993
██████████████████████████████
                      1994
██████████████████████████████
██████████████████████████████
              1995
██████████████████████████████
██████████████████████████████
      1996
██████████████████████████████
     2026
██████████████████████████████
█████████████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ← lived (█) gives way to remaining (▓)
    2027
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
   2082
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

In a real terminal the lived weeks are bright teal, remaining weeks fade gently
toward slate, and the week containing *today* glows amber.

**Views**

- `grid` — the life-in-weeks grid (default)
- `ratio` — a single horizontal bar of lived-vs-remaining time
- `stats` — a numeric breakdown: weeks/months/years counts, the quarter- and
  half-life milestones, and when your weeks run out

## Usage

```bash
python3 lifegrid.py --born 1993-01-01 --lifespan 90
python3 lifegrid.py --born 1993-01-01 --view stats
python3 lifegrid.py --born 1993-01-01 --view ratio --width 80

# And the other way around — the grid accepts any ISO date:
python3 lifegrid.py --born 1993-01-01 --lifespan 90 --view grid
```

| Flag | Meaning | Default |
|------|---------|---------|
| `--born` | Your birth date (ISO `YYYY-MM-DD`) | required |
| `--lifespan` | Assumed total years you'll live | `90` |
| `--view` | `grid` \| `ratio` \| `stats` | `grid` |
| `--width` | Characters wide for `grid`/`ratio` | terminal width |

## Design notes

- **No dependencies** — `argparse`, `datetime`, `math`, and ANSI escapes only.
- **True-color aware** — if `$NO_COLOR` is set or output isn't a TTY, it falls
  back to plain ASCII so it's pipe-friendly.
- **It's a mirror, not a prophecy.** The lifespan is your own input, and the
  colorful "past" is just the time you've already spent. The useful number is
  the other one.
