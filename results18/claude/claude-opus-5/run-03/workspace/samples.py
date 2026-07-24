"""Hand-drawn sample textures for the WFC synthesiser.

Each sample carries the options that suit it.

Symmetry is the subtle one: the dihedral variants rearrange characters but do not
remap them, so a rotated run of `━` is a *vertical* run of horizontal glyphs.
Only samples drawn from orientation-free characters (`#`, `~`, `░`) may use the
full 8-fold group; anything using box-drawing or directional glyphs must use 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sample:
    name: str
    blurb: str
    rows: tuple[str, ...]
    size: int = 3
    symmetry: int = 8
    periodic_input: bool = True
    # char -> ANSI 256-colour index, for terminal rendering
    palette: dict[str, int] = field(default_factory=dict)


def _rows(block: str) -> tuple[str, ...]:
    """Drop the block's own newlines and pad every row to the widest one.

    Only one newline is removed from each end, so a deliberately blank row
    (MEADOW's sky) survives and becomes a row of spaces.
    """
    lines = block.removeprefix("\n").removesuffix("\n").split("\n")
    width = max(len(line) for line in lines)
    return tuple(line.ljust(width) for line in lines)


ISLAND = Sample(
    name="island",
    blurb="archipelagos with graded shorelines",
    rows=_rows("""
~~~~~~~~~~~~~~~~
~~~~~~····~~~~~~
~~~~··:::·~~~~~~
~~~·::###::·~~~~
~~··:#####:·~~~~
~~·::#####::·~~~
~~~·::###::·~~~~
~~~~·:::··~~~~~~
~~~~~····~~~~~~~
~~~~~~~~~~~~~~~~
"""),
    palette={"~": 25, "·": 179, ":": 143, "#": 65},
)

CAVE = Sample(
    name="cave",
    blurb="cellular caverns, walls and rubble",
    rows=_rows("""
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▒▒░░░░▒▒▓▓▓▓▓▓
▓▒░░    ░░▒▒▓▓▓▓
▓▒░  ░░   ░▒▓▓▓▓
▓▒░ ░▒▒░  ░░▒▓▓▓
▓▓▒░░▒▓▒░░  ░▒▓▓
▓▓▓▒▒▒▓▓▒░   ░▒▓
▓▓▓▓▓▓▓▓▒░░  ░▒▓
▓▓▓▓▓▓▓▓▓▒░░░░▒▓
▓▓▓▓▓▓▓▓▓▓▒▒▒▒▓▓
"""),
    palette={"▓": 238, "▒": 245, "░": 250, " ": 16},
)

MAZE = Sample(
    name="maze",
    blurb="perfect-maze corridors, one cell wide",
    rows=_rows("""
#########################
#   #       #     #     #
# # # ##### # ### # ### #
# #   #   # # # # #   # #
# ##### # # # # # ##### #
#       # #   #       # #
######### ##### ##### # #
#       #     #     # # #
# ##### ##### ##### # # #
#     #     #     #   # #
#########################
"""),
    periodic_input=False,
    palette={"#": 60, " ": 16},
)

LABYRINTH = Sample(
    name="labyrinth",
    blurb="nested box-drawing corridors",
    rows=_rows("""
┌──────────┐
│┌────────┐│
││┌──────┐││
│││┌────┐│││
││││┌──┐││││
││││└──┘││││
│││└────┘│││
││└──────┘││
│└────────┘│
└──────────┘
"""),
    symmetry=1,
    periodic_input=False,
    palette={"─": 109, "│": 109, "┌": 152, "┐": 152, "└": 152, "┘": 152, " ": 16},
)

MEADOW = Sample(
    name="meadow",
    blurb="flowers over soil — gravity is respected",
    rows=_rows("""


        ✿     ✿
   ✿    │  ✿  │
   │    │  │  │  ✿
 ✿ │ ✿  │  │  │  │
 │ │ │  │  │  │  │
▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚▚
▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞▞
"""),
    symmetry=1,
    periodic_input=False,
    palette={"✿": 211, "│": 71, "▚": 94, "▞": 58, " ": 16},
)

CIRCUIT = Sample(
    name="circuit",
    blurb="traces, junctions and pads",
    rows=_rows("""
·············┃········
·╺━━━━┓······┃···╻····
······┃······┃···┃····
██····┣━━━━━━╋━━━┛····
······┃······┃········
·╺━━━━┛······┃···████·
·············┃···████·
·······┏━━━━━╋━━━━━━╸·
·······╹·····┃········
·············┃········
"""),
    symmetry=1,
    palette={
        "·": 22, "━": 220, "┃": 220, "╋": 226, "┣": 226, "┓": 220,
        "┛": 220, "┏": 220, "╺": 214, "╸": 214, "╻": 214, "╹": 214, "█": 178,
    },
)

SAMPLES = {s.name: s for s in (ISLAND, CAVE, MAZE, LABYRINTH, MEADOW, CIRCUIT)}
