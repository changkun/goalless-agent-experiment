#!/usr/bin/env python3
"""Terminal ASCII Art Clock — displays current time in big block digits."""

import time
import sys

# Each digit is 5 rows × 5 cols
DIGITS = {
    '0': [
        " ███ ",
        "█   █",
        "█   █",
        "█   █",
        " ███ ",
    ],
    '1': [
        "  █  ",
        " ██  ",
        "  █  ",
        "  █  ",
        " ███ ",
    ],
    '2': [
        " ███ ",
        "█   █",
        "  ██ ",
        " █   ",
        "█████",
    ],
    '3': [
        "█████",
        "    █",
        " ███ ",
        "    █",
        "█████",
    ],
    '4': [
        "█   █",
        "█   █",
        "█████",
        "    █",
        "    █",
    ],
    '5': [
        "█████",
        "█    ",
        "████ ",
        "    █",
        "████ ",
    ],
    '6': [
        " ███ ",
        "█    ",
        "████ ",
        "█   █",
        " ███ ",
    ],
    '7': [
        "█████",
        "    █",
        "   █ ",
        "  █  ",
        "  █  ",
    ],
    '8': [
        " ███ ",
        "█   █",
        " ███ ",
        "█   █",
        " ███ ",
    ],
    '9': [
        " ███ ",
        "█   █",
        " ████",
        "    █",
        " ███ ",
    ],
}

COLON = [
    "   ",
    " ● ",
    "   ",
    " ● ",
    "   ",
]

SHADE = "█"

def render_time(timestr):
    """Render HH:MM as a 5-row ASCII art string."""
    h1, h2, _, m1, m2 = timestr
    rows = []
    for i in range(5):
        parts = [
            DIGITS[h1][i],
            " ",
            DIGITS[h2][i],
            "  ",
            COLON[i],
            "  ",
            DIGITS[m1][i],
            " ",
            DIGITS[m2][i],
        ]
        rows.append("".join(parts))
    return rows


def main():
    use_color = sys.stdout.isatty()
    clear = "\033[2J\033[H" if use_color else ""
    width = 37

    try:
        while True:
            now = time.strftime("%H:%M")
            rows = render_time(now)
            date_str = time.strftime("%A, %B %d, %Y")

            if use_color:
                sys.stdout.write(clear)
                print(f"\033[1;36m{'━' * width}\033[0m")
                print(f"\033[1;33m{'⏰  TERMINAL CLOCK  ⏰':^{width}}\033[0m")
                print(f"\033[1;36m{'━' * width}\033[0m")
                print()
                for row in rows:
                    print(f"\033[1;32m{row:^{width}}\033[0m")
                print()
                print(f"\033[90m{date_str:^{width}}\033[0m")
                print(f"\033[1;36m{'━' * width}\033[0m")
            else:
                print("=" * width)
                print(f"{'TERMINAL CLOCK':^{width}}")
                print("=" * width)
                print()
                for row in rows:
                    print(f"{row:^{width}}")
                print()
                print(f"{date_str:^{width}}")
                print("=" * width)
                break

            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        if use_color:
            sys.stdout.write("\033[2J\033[H")
            print("\033[1;33m  Goodbye! 👋\033[0m")


if __name__ == "__main__":
    main()
