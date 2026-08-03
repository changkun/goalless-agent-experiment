"""Affirmation and ASCII art bank for the peak CLI."""

AFFIRMATIONS = [
    "Discipline is choosing what you want most over what you want now.",
    "Small steps every day become big results over time.",
    "You don't need to be perfect, just a little better than yesterday.",
    "The grind is hard, but so are you.",
    "Progress, not perfection.",
    "Show up even when motivation doesn't.",
    "You've survived 100% of your hardest days so far.",
]

ART = r"""
      /\
     /  \
    / /\ \
   / ____ \
  /_/    \_\
    PEAK
"""


def random_affirmation(rng):
    return rng.choice(AFFIRMATIONS)
