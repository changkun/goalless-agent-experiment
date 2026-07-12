"""A self-similar poem.

The poem is a 5-line piece. Line 1 names the whole. Line 2 states a
property of the whole. Line 3 is the whole compressed. Line 4 echoes
line 2 in a smaller key. Line 5 echoes line 1 — the whole, returned.

The trick is that the *same* template generates a poem about the
Mandelbrot set, a poem about the year, and a poem about itself.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stanza:
    whole: str       # a name for the whole (line 1, repeated in line 5)
    property: str    # a property of the whole (line 2, repeated as line 4)
    middle: str      # the whole in one line (line 3)

    def lines(self) -> tuple[str, str, str, str, str]:
        # The stanza is a palindrome: line 1 == line 5, line 2 == line 4.
        # The middle line is the whole compressed.
        return (
            f"the {self.whole} is a {self.whole}.",
            f"and every {self.whole} {self.property}.",
            self.middle,
            f"and every {self.whole} {self.property}.",
            f"the {self.whole} is a {self.whole}.",
        )


def recite() -> str:
    """Recite the default 3-stanza poem. Each stanza is one fractal."""
    stanzas = [
        Stanza(
            whole="set",
            property="contains a coast",
            middle="a coast, then a coast, then a coast — all the way down.",
        ),
        Stanza(
            whole="year",
            property="turns a day",
            middle="a day, then a day, then a day — all the way down.",
        ),
        Stanza(
            whole="poem",
            property="says the poem",
            middle="a line, then a line, then a line — all the way down.",
        ),
    ]
    out: list[str] = []
    for s in stanzas:
        out.extend(s.lines())
        out.append("")  # blank line between stanzas
    return "\n".join(out).rstrip()
