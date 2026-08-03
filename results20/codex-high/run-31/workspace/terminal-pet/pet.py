#!/usr/bin/env python3
"""A tiny terminal pet: hatch an egg, feed it, play with it, and watch it grow."""

import argparse
import random


EGG = r"""
   ____
  /    \
 |  o o |
 |   ^  |
  \____/
"""


def face(happiness, fullness, energy, sleeping):
    if sleeping:
        return "zZz"
    if happiness < 30:
        return ">_<"
    if fullness < 30:
        return "o_o"
    if energy < 30:
        return "-_-"
    return "^_^"


def draw_pet(stage, happiness, fullness, energy, sleeping):
    f = face(happiness, fullness, energy, sleeping)
    if stage == "egg":
        return EGG
    if stage == "baby":
        return f"""
   ,--.
   |{f}|
  (  v  )
   ---
  / | | \\"""
    return f"""
   /\\_/\\
  ( {f} )
  (  u  )  <-- adult
   ===
  /| | |\\"""


def show_stats(stage, egg_ticks, age, happiness, fullness, energy):
    print(f"stage: {stage}   age: {age // 4}h")
    if stage == "egg":
        print(f"the egg is wiggling... hatching in ~{max(egg_ticks, 0)} steps")
    print(f"happiness: {'▓' * (happiness // 10)}{'░' * (10 - happiness // 10)} {happiness}")
    print(f"fullness : {'▓' * (fullness // 10)}{'░' * (10 - fullness // 10)} {fullness}")
    print(f"energy   : {'▓' * (energy // 10)}{'░' * (10 - energy // 10)} {energy}")


def main():
    parser = argparse.ArgumentParser(description="A tiny terminal pet.")
    parser.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["status", "feed", "play", "sleep", "wake"],
        help="what to do with your pet",
    )
    args = parser.parse_args()

    # Toy state; real persistence would live in a file.
    age = random.randint(0, 40)
    stage = "adult" if age > 20 else ("baby" if age > 8 else "egg")
    egg_ticks = random.randint(2, 6) if stage == "egg" else 0
    happiness = random.randint(50, 80)
    fullness = random.randint(50, 80)
    energy = random.randint(50, 80)
    sleeping = False

    if args.action == "feed":
        fullness = min(100, fullness + 25)
        happiness = min(100, happiness + 5)
        print("You offer a snack. Nom nom nom!")
    elif args.action == "play":
        happiness = min(100, happiness + 30)
        energy = max(0, energy - 15)
        fullness = max(0, fullness - 5)
        print("You toss a ball. It bounces everywhere!")
    elif args.action == "sleep":
        sleeping = True
        energy = min(100, energy + 20)
        print("It curls up and dozes off. zZz")
    elif args.action == "wake":
        sleeping = False
        energy = max(0, energy - 5)
        print("It stirs and blinks awake.")

    age += 1
    fullness = max(0, fullness - 2)
    energy = max(0, energy - 1)

    if stage == "egg" and egg_ticks <= 0:
        stage = "baby"
    elif stage == "egg":
        egg_ticks -= 1
    elif age > 20:
        stage = "adult"
    elif age > 8:
        stage = "baby"

    print(draw_pet(stage, happiness, fullness, energy, sleeping))
    show_stats(stage, egg_ticks, age, happiness, fullness, energy)


if __name__ == "__main__":
    main()
