#!/usr/bin/env python3
"""Print a random friendly greeting with ASCII art."""

import random

CREATURES = [
    (
        "cat",
        r"""
    /\_____/\
   /  o   o  \
  ( ==  ^  == )
   )         (
  (           )
 ( (  )   (  ) )
(__(__)___(__)__)
""",
    ),
    (
        "dog",
        r"""
   __
o-''|\_____/)
 \_/|_)     )
    \  __  /
    (_/ (_/
""",
    ),
    (
        "robot",
        r"""
    [_____]
    |+   +|
    |  o  |
    |_____|
   /|=====|\
  / |=====| \
 /  |=====|  \
""",
    ),
    (
        "bunny",
        r"""
  /\   /\
 (  \ /  )
  >  X   <
 (  / \  )
  \/   \/
""",
    ),
]

MESSAGES = [
    "Hope you're having a great day!",
    "You're doing better than you think.",
    "Keep going — you've got this.",
    "One small step is still progress.",
    "Thanks for taking a moment to say hi.",
]


def main() -> None:
    name, art = random.choice(CREATURES)
    message = random.choice(MESSAGES)
    print(f"Hello from the {name}!\n{art}\n{message}")


if __name__ == "__main__":
    main()
