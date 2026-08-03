"""A small, encrypted password store backed by a single JSON file.

Secrets live in a ChaCha20-Poly1305 encrypted blob (see :mod:`passgen.cipher`).
In memory, the vault keeps a mapping of name -> dict of key/value fields.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any

from .cipher import decrypt, encrypt

Record = dict[str, str]


@dataclass
class Vault:
    """An in-memory view over an encrypted store.

    Attributes:
        path: filesystem location of the encrypted store (created on save).
        data: mapping of entry name to records.
        password: master password used to (de)crypt the store (stored in
            memory only, never persisted).
    """

    path: str
    data: dict[str, Record]
    password: str
    _dirty: bool = False

    @classmethod
    def open(cls, path: str, password: str) -> "Vault":
        """Open an existing vault, or create an empty one if absent."""
        if os.path.exists(path):
            with open(path, "rb") as handle:
                blob = handle.read()
            raw = decrypt(blob, password)
            data = json.loads(raw.decode("utf-8"))
            return cls(path=path, data=data, password=password)
        return cls(path=path, data={}, password=password)

    def set(self, name: str, **fields: str) -> None:
        """Create or update an entry with the given string fields."""
        self.data[name] = {k: v for k, v in fields.items()}
        self._dirty = True

    def get(self, name: str) -> Record | None:
        """Return a copy of an entry, or None if missing."""
        entry = self.data.get(name)
        return dict(entry) if entry is not None else None

    def delete(self, name: str) -> bool:
        """Remove an entry; returns True if it existed."""
        removed = self.data.pop(name, None)
        if removed is not None:
            self._dirty = True
            return True
        return False

    def names(self) -> list[str]:
        """Return entry names in sorted order."""
        return sorted(self.data)

    def save(self) -> None:
        """Atomically write the encrypted store to disk."""
        raw = json.dumps(self.data, indent=2, sort_keys=True).encode("utf-8")
        blob = encrypt(raw, self.password)
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".vault-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(blob)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._dirty = False

    def change_password(self, new_password: str) -> None:
        """Re-encrypt the store under a new password."""
        self.password = new_password
        self._dirty = True
