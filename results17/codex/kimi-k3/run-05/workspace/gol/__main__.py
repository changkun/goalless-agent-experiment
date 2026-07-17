"""Command line: python3 -m gol <command> [options]"""
import argparse
import random
import sys

from . import patterns
from .grid import Grid
from .render import render_poster
from .sim import Simulation, soup_grid, sparkline


def cmd_run(args):
    grid = Grid(args.w, args.h)
    if args.pattern:
        cells = patterns.get(args.pattern)
        pw = max(c[0] for c in cells) + 1
        ph = max(c[1] for c in cells) + 1
        ox = max(0, (args.w - pw) // 2)
        oy = max(0, (args.h - ph) // 2)
        patterns.stamp(grid, args.pattern, ox, oy)
    else:
        grid = soup_grid(args.w, args.h, args.density, random.Random(args.seed))
    sim = Simulation(grid, rule=args.rule)
    label = args.pattern or f"soup d={args.density} seed={args.seed}"
    print(f"grid {args.w}x{args.h}  rule {args.rule}  {label}")
    print(f"t=0  pop={grid.population()}")
    print(grid.ascii())
    for i in range(args.ticks):
        sim.step()
        if args.every and (i + 1) % args.every == 0:
            print(f"\nt={sim.tick_count}  pop={grid.population()}")
            print(grid.ascii())
    print(f"\nfinal: t={sim.tick_count}  pop={grid.population()}")


def cmd_soup(args):
    rng = random.Random(args.seed)
    print(f"running {args.n} soups ({args.w}x{args.h}, density {args.density}, "
          f"rule {args.rule}, cap {args.max_ticks} ticks)")
    outcomes = {"extinct": [], "cycle": [], "timeout": []}
    for i in range(args.n):
        grid = soup_grid(args.w, args.h, args.density, rng)
        sim = Simulation(grid, rule=args.rule)
        outcome, detail = sim.run_until_settled(args.max_ticks)
        outcomes[outcome].append(detail)
        if outcome == "cycle":
            period, tick = detail
            print(f"  soup {i + 1}: cycle period={period} settled@{tick}")
        elif outcome == "extinct":
            print(f"  soup {i + 1}: extinct @{detail}")
        else:
            print(f"  soup {i + 1}: still churning @{detail}")
    print("\nsummary:")
    print(f"  extinct : {len(outcomes['extinct'])}")
    print(f"  cycle   : {len(outcomes['cycle'])}")
    print(f"  churning: {len(outcomes['timeout'])}")


def cmd_series(args):
    grid = soup_grid(args.w, args.h, args.density, random.Random(args.seed))
    if args.pattern:
        grid = Grid(args.w, args.h)
        patterns.stamp(grid, args.pattern, args.w // 4, args.h // 4)
    sim = Simulation(grid, rule=args.rule)
    series = sim.population_series(args.ticks)
    print(f"population over {args.ticks} ticks (rule {args.rule})")
    print(sparkline(series, width=min(70, args.ticks)))
    print(f"min={min(series)} max={max(series)} final={series[-1]}")


def cmd_poster(args):
    rng = random.Random(args.seed)
    if args.pattern:
        grid = Grid(args.w, args.h)
        patterns.stamp(grid, args.pattern, 2, max(2, args.h // 3))
        title = args.title or args.pattern.replace("_", " ").upper()
    else:
        grid = soup_grid(args.w, args.h, args.density, rng)
        title = args.title or f"SOUP {args.seed}"
    sim = Simulation(grid, rule=args.rule)
    subtitle = f"RULE {args.rule.replace('/', ' / ')}"
    gaps = [max(1, args.ticks // args.frames)] * args.frames
    ticks = render_poster(
        sim, gaps, args.out,
        palette_name=args.palette, cell_px=args.cell_px,
        title=title, subtitle=subtitle,
    )
    print(f"wrote {args.out}  (frames at ticks {ticks})")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gol", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--rule", default="B3/S23")
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--w", type=int, default=48)
        p.add_argument("--h", type=int, default=28)
        p.add_argument("--density", type=float, default=0.22)
        p.add_argument("--pattern", default=None,
                       help=f"one of: {', '.join(sorted(patterns.PATTERNS))}")

    p = sub.add_parser("run", help="simulate and print ASCII frames")
    common(p)
    p.add_argument("--ticks", type=int, default=20)
    p.add_argument("--every", type=int, default=5)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("soup", help="run random soups, report how they die")
    common(p)
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--max-ticks", type=int, default=3000)
    p.set_defaults(func=cmd_soup)

    p = sub.add_parser("series", help="population sparkline for one run")
    common(p)
    p.add_argument("--ticks", type=int, default=200)
    p.set_defaults(func=cmd_series)

    p = sub.add_parser("poster", help="render a titled poster PNG")
    common(p)
    p.add_argument("--frames", type=int, default=3)
    p.add_argument("--ticks", type=int, default=90)
    p.add_argument("--palette", default="phosphor")
    p.add_argument("--cell-px", type=int, default=10)
    p.add_argument("--title", default=None)
    p.add_argument("--out", default="poster.png")
    p.set_defaults(func=cmd_poster)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
