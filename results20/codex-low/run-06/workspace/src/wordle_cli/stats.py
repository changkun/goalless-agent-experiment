"""Session statistics persisted as JSON."""
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

DEFAULT_STATS = {
    "games_played": 0,
    "games_won": 0,
    "current_streak": 0,
    "max_streak": 0,
    "guess_distribution": {},  # attempts -> count
    "last_played": None,
}


@dataclass
class Stats:
    games_played: int = 0
    games_won: int = 0
    current_streak: int = 0
    max_streak: int = 0
    guess_distribution: dict = None
    last_played: str = None

    def __post_init__(self):
        if self.guess_distribution is None:
            self.guess_distribution = {}


def stats_path() -> Path:
    base = os.environ.get("WORDLE_DATA_DIR")
    if base:
        return Path(base) / "stats.json"
    return Path.home() / ".wordle_cli" / "stats.json"


def load_path(path: Path) -> Stats:
    if not path.exists():
        return Stats()
    try:
        data = json.loads(path.read_text())
        return Stats(**{**DEFAULT_STATS, **data})
    except (json.JSONDecodeError, TypeError):
        return Stats()


def load() -> Stats:
    return load_path(stats_path())


def record(result: dict, path: Optional[Path] = None) -> Stats:
    """Update and save stats from a game result.

    result keys: won (bool), attempts (int).
    """
    target = path or stats_path()
    stats = load_path(target) if target.exists() else Stats()
    stats.games_played += 1
    if result.get("won"):
        stats.games_won += 1
        stats.current_streak += 1
        stats.max_streak = max(stats.max_streak, stats.current_streak)
        dist = stats.guess_distribution
        attempts = result.get("attempts", 0)
        dist[str(attempts)] = dist.get(str(attempts), 0) + 1
    else:
        stats.current_streak = 0
    stats.last_played = time.strftime("%Y-%m-%d %H:%M:%S")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(stats), indent=2))
    return stats
