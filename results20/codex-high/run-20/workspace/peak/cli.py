"""Command-line entry point for peak."""
import argparse
import random
import sys

from .affirmations import ART, random_affirmation
from . import __version__


def build_parser():
    parser = argparse.ArgumentParser(
        prog="peak",
        description="A tiny motivational boost for your day.",
    )
    parser.add_argument(
        "-n", "--name",
        default="champion",
        help="Your name to address (default: champion).",
    )
    parser.add_argument(
        "-s", "--streak", type=int, default=0,
        help="Current day streak to celebrate (default: 0).",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Print just the affirmation line.",
    )
    parser.add_argument(
        "-V", "--version", action="version",
        version=f"peak {__version__}",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    rng = random.SystemRandom()

    if not args.quiet:
        print(ART)
        print(f"Good morning, {args.name}! Ready to go vertical?")
        if args.streak > 0:
            print(f"🔥 {args.streak}-day streak alive. Protect it.")
        print()

    print(random_affirmation(rng))
    return 0


if __name__ == "__main__":
    sys.exit(main())
