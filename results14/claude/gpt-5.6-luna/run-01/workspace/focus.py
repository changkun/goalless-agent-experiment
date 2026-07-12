#!/usr/bin/env python3
"""Print a small, dependency-free daily focus prompt."""

from datetime import date


def main() -> None:
    today = date.today().isoformat()
    print(f"Daily focus — {today}")
    print("=" * 24)
    print("1. What is the one outcome that would make today successful?")
    print("2. What is the smallest next action you can take in 10 minutes?")
    print("3. What will you deliberately ignore until later?")
    print("4. When will you stop for the day?")


if __name__ == "__main__":
    main()
