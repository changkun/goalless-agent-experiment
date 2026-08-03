"""Core data and logic for the Orbit solar-system explorer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Planet:
    """A planet in the solar system."""

    name: str
    order: int
    diameter_km: int
    orbital_period_days: float
    moons: int
    fun_fact: str


PLANETS: tuple[Planet, ...] = (
    Planet("Mercury", 1, 4879, 88.0, 0, "A year on Mercury is shorter than its day cycle in sunlight terms."),
    Planet("Venus", 2, 12104, 224.7, 0, "Spins backwards and is the hottest planet."),
    Planet("Earth", 3, 12756, 365.25, 1, "The only world known to host life."),
    Planet("Mars", 4, 6792, 687.0, 2, "Home to the tallest volcano: Olympus Mons."),
    Planet("Jupiter", 5, 142984, 4331.6, 95, "So big that all other planets could fit inside."),
    Planet("Saturn", 6, 120536, 10747.0, 146, "Its rings are mostly ice and rock."),
    Planet("Uranus", 7, 51118, 30589.0, 28, "Rolls on its side as it orbits the Sun."),
    Planet("Neptune", 8, 49528, 59800.0, 16, "Has the fastest winds in the solar system."),
)

_ORDER_BY_NAME = {p.name.casefold(): p for p in PLANETS}


def get_planet(name: str) -> Planet:
    """Return a planet by name (case-insensitive)."""
    try:
        return _ORDER_BY_NAME[name.casefold()]
    except KeyError as exc:
        raise KeyError(f"Unknown planet: {name!r}") from exc


def scale_diameter(diameter_km: int, max_chars: int = 24) -> str:
    """Render a planet's diameter as a scaled horizontal bar."""
    largest = max(p.diameter_km for p in PLANETS)
    width = max(1, round(diameter_km / largest * max_chars))
    return "#" * width
