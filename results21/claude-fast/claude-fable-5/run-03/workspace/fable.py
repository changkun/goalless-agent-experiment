#!/usr/bin/env python3
"""fable.py — a tiny procedural fable generator.

Composes Aesop-style fables from a weighted grammar: two animals with
opposing temperaments, a setting, a complication, a reversal, and a moral
that actually follows from the reversal (morals are keyed to plot shape,
not chosen at random — that's the whole trick).

Usage:
    python3 fable.py [seed]

Each seed is a different fable. No seed means a random one.
"""

import random
import sys
import textwrap

ANIMALS = [
    ("Fox", "clever", "cleverness"),
    ("Tortoise", "patient", "patience"),
    ("Crow", "vain", "vanity"),
    ("Ant", "industrious", "industry"),
    ("Hare", "boastful", "boastfulness"),
    ("Owl", "cautious", "caution"),
    ("Wolf", "greedy", "greed"),
    ("Mouse", "humble", "humility"),
    ("Peacock", "proud", "pride"),
    ("Heron", "picky", "pickiness"),
    ("Beaver", "diligent", "diligence"),
    ("Magpie", "curious", "curiosity"),
]

SETTINGS = [
    "at the edge of a drying riverbed",
    "beneath the great oak at the crossroads",
    "in an orchard heavy with late fruit",
    "on the frost-silvered morning of first snow",
    "beside a well whose rope had rotted through",
    "in a meadow the farmer had forgotten to mow",
    "on the narrow bridge over the millstream",
    "in the granary, after the harvest was counted",
]

TREASURES = [
    "a single perfect fig",
    "the last acorn of autumn",
    "a scrap of honeycomb",
    "a fallen star, still warm",
    "the key to the farmer's gate",
    "a mirror-smooth pebble",
    "the only dry burrow before the rains",
    "a song neither of them had heard before",
]

# Each plot shape pairs a reversal template with morals that follow from it.
PLOTS = [
    {
        "reversal": (
            "But in reaching for it, the {a1} lost footing and tumbled, and it was "
            "the {a2} — {t2} as ever — who caught both {a1} and prize, and shared the latter freely."
        ),
        "morals": [
            "What {v1} grasps, {v2} keeps.",
            "The surest hands are the ones not trembling with want.",
        ],
    },
    {
        "reversal": (
            "So the {a2} simply waited. By dusk the {a1}'s {v1} had done all the work of ruin "
            "on its own, and the prize rolled quietly to where the {a2} sat."
        ),
        "morals": [
            "{v1c} defeats itself; {v2} need only stand nearby.",
            "Time is the ally of those who do not argue with it.",
        ],
    },
    {
        "reversal": (
            "In the end they divided it — not because either wished to, but because the crows were "
            "circling, and even a {t1} {a1} can count. Splitting the prize, they kept it; "
            "fighting, they would have fed the sky."
        ),
        "morals": [
            "Half a prize is a feast beside a whole one lost.",
            "Enemies who share a danger had better share a table.",
        ],
    },
    {
        "reversal": (
            "The {a1} won it outright, fair and square — and found it far too heavy to carry home. "
            "The {a2}, following at a distance, carried nothing and arrived with everything."
        ),
        "morals": [
            "Winning is a question; keeping is the answer.",
            "Do not envy the winner until you have seen the road home.",
        ],
    },
]

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
  <rect width="640" height="360" fill="{sky}"/>
  <circle cx="{sunx}" cy="70" r="34" fill="{sun}" opacity="0.9"/>
  {hills}
  {trees}
  <ellipse cx="{px}" cy="300" rx="10" ry="6" fill="{prize}"/>
  <text x="320" y="342" text-anchor="middle" font-family="Georgia, serif" font-size="15" fill="{ink}" font-style="italic">{caption}</text>
</svg>
"""


def make_scene(rng, title):
    """A little generative landscape: layered hills, scattered trees, one prize."""
    palettes = [
        ("#f4e8d0", "#e8b04b", "#8a9a5b", "#5b6e3a", "#3d4d28", "#4a3728"),  # afternoon
        ("#dce7f0", "#f0d9a0", "#7d94a8", "#54708a", "#39506b", "#2e3a48"),  # frost morning
        ("#f7d9c4", "#e07a5f", "#9c8f5f", "#6f6a3d", "#4d4a2a", "#3f2e24"),  # dusk
    ]
    sky, sun, h1, h2, h3, ink = rng.choice(palettes)

    hills = []
    for i, (col, base) in enumerate([(h1, 250), (h2, 275), (h3, 300)]):
        pts = [f"0,{360}"]
        x = 0
        y = base + rng.randint(-10, 10)
        while x <= 640:
            pts.append(f"{x},{y}")
            x += rng.randint(60, 120)
            y = base + rng.randint(-28, 18)
        pts.append("640,360")
        hills.append(f'<polygon points="{" ".join(pts)}" fill="{col}"/>')

    trees = []
    for _ in range(rng.randint(3, 7)):
        tx = rng.randint(30, 610)
        ty = rng.randint(255, 300)
        s = rng.uniform(0.6, 1.3)
        trees.append(
            f'<g transform="translate({tx},{ty}) scale({s:.2f})">'
            f'<rect x="-2" y="-4" width="4" height="16" fill="{ink}"/>'
            f'<circle cy="-14" r="12" fill="{h3}"/></g>'
        )

    return SVG_TEMPLATE.format(
        sky=sky, sun=sun, ink=ink,
        sunx=rng.randint(80, 560),
        px=rng.randint(100, 540),
        prize="#d4a017",
        hills="\n  ".join(hills),
        trees="\n  ".join(trees),
        caption=title,
    )


def an(word):
    return ("an " if word[0].lower() in "aeiou" else "a ") + word


def make_fable(seed=None):
    rng = random.Random(seed)
    (a1, t1, v1), (a2, t2, v2) = rng.sample(ANIMALS, 2)
    setting = rng.choice(SETTINGS)
    treasure = rng.choice(TREASURES)
    plot = rng.choice(PLOTS)

    ctx = dict(a1=a1, a2=a2, t1=t1, t2=t2, v1=v1, v2=v2,
               v1c=v1.capitalize())

    title = f"The {a1} and the {a2}"
    opening = (
        f"One day {setting}, {an(t1)} {a1} and {an(t2)} {a2} "
        f"came upon {treasure} at the very same moment."
    )
    middle = (
        f"\"It is mine,\" said the {a1}, \"for I saw it first.\" "
        f"\"It is mine,\" said the {a2}, \"for I stand nearer.\" "
        f"And neither would yield so much as a whisker's width."
    )
    reversal = plot["reversal"].format(**ctx)
    moral = rng.choice(plot["morals"]).format(**ctx)

    body = "\n\n".join(
        textwrap.fill(p, width=72) for p in (opening, middle, reversal)
    )
    text = f"{title}\n{'=' * len(title)}\n\n{body}\n\nMoral: {moral}\n"
    svg = make_scene(rng, title)
    return title, text, svg


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10**6)
    title, text, svg = make_fable(seed)
    print(text)
    print(f"(seed {seed})")
    slug = title.lower().replace(" ", "-")
    out = f"{slug}.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"illustration: {out}")
