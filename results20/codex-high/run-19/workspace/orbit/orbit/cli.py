"""Command-line interface for Orbit."""

from __future__ import annotations

import argparse
import sys

from .core import PLANETS, Planet, get_planet, scale_diameter


def format_planet(planet: Planet) -> str:
    """Return a formatted block for a single planet."""
    lines = [
        f"{planet.order}. {planet.name}",
        f"   Diameter : {planet.diameter_km:,} km  {scale_diameter(planet.diameter_km)}",
        f"   Year     : {planet.orbital_period_days:,.1f} days",
        f"   Moons    : {planet.moons}",
        f"   Did you know? {planet.fun_fact}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orbit",
        description="Explore the solar system from your terminal.",
    )
    parser.add_argument(
        "planet",
        nargs="*",
        help="Optional planet name(s) to show; show all by default.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.planet:
        names: list[str] = []
        for name in args.planet:
            try:
                names.append(get_planet(name).name)
            except KeyError as exc:
                print(f"error: {exc}", file=sys.stderr)
        if not names:
            return 1
        targets = [get_planet(n) for n in names]
    else:
        targets = list(PLANETS)

    for planet in targets:
        print(format_planet(planet))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
