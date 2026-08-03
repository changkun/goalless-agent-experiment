"""Persistence layer for streak data.

Data is kept in a single JSON file. Each habit maps to a list of ISO date
strings (e.g. "2026-08-03") recording days on which the habit was checked.
"""

import json
import os
from dataclasses import dataclass, field

DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".streaks.json")


@dataclass
class Store:
    path: str = DEFAULT_PATH
    data: dict = field(default_factory=dict)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
                if isinstance(loaded, dict):
                    self.data = loaded
        return self

    def save(self):
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=True)
        os.replace(tmp, self.path)

    def habits(self):
        return sorted(self.data.keys())

    def add_habit(self, name):
        self.data.setdefault(name, [])
        return self

    def check(self, name, date):
        if name not in self.data:
            self.data[name] = []
        if date not in self.data[name]:
            self.data[name].append(date)
            self.data[name].sort()
        return self

    def uncheck(self, name, date):
        dates = self.data.get(name, [])
        if date in dates:
            dates.remove(date)
        return self
