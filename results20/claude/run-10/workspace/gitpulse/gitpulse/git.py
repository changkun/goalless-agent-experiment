"""Read commit history via git plumbing without any external dependencies."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import List

from .analyzer import Commit
from .errors import NotAGitRepo

# A raw, machine-readable commit stream. `%aI` is author date as strict ISO,
# `%h` short hash, `%aN` author name, `%aE` author email. Insertion/deletion
# counts come from a separate `--shortstat` line we parse per commit.
_SEP = "\x1e"
_FIELD = "\x1f"


def _run_git(repo: str, args: List[str], check: bool = True) -> str:
    """Run a git command inside `repo` and return its stdout as text."""
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - git always present in tests
        raise NotAGitRepo(repo) from exc
    if not check and proc.returncode != 0:
        return ""
    if proc.returncode != 0:
        raise NotAGitRepo(repo)
    return proc.stdout


def is_repo(repo: str) -> bool:
    """Return True if `repo` is inside a git working tree."""
    try:
        _run_git(repo, ["rev-parse", "--is-inside-work-tree"])
        return True
    except NotAGitRepo:
        return False


def current_branch(repo: str) -> str:
    """Return the current branch name, or an empty string if detached."""
    stdout = _run_git(repo, ["symbolic-ref", "--short", "-q", "HEAD"])
    return stdout.strip()


def load_commits(repo: str, *, limit: int | None = None) -> List[Commit]:
    """Fetch commit metadata for the current branch of `repo`."""

    def parse_shortstat(text: str) -> tuple[int, int]:
        inserts = deletes = 0
        for part in text.split(","):
            chunk = part.strip()
            if "insertion" in chunk:
                inserts = int(chunk.split()[0])
            elif "deletion" in chunk:
                deletes = int(chunk.split()[0])
        return inserts, deletes

    args = [
        "log",
        "--pretty=format:%x1e%h%x1f%aN%x1f%aE%x1f%aI%x1f%x1e",
        "--shortstat",
        "--no-merges",
    ]
    if limit:
        args += ["-n", str(limit)]
    raw = _run_git(repo, args)

    commits: List[Commit] = []
    header = None
    # NOTE: split on "\n" only. splitlines() would also split on \x1e/\x1f
    # (record/unit separators), which our delimiters rely on.
    for line in raw.split("\n"):
        if line.startswith(_SEP) and line.count(_FIELD) >= 3:
            # A record is wrapped in \x1e, fields joined by \x1f.
            body = line.strip(_SEP)
            sha, author, email, when, *_ = body.split(_FIELD)
            header = (sha, author, email, datetime.fromisoformat(when))
        elif line.strip() and header is not None:
            ins, dele = parse_shortstat(line)
            sha, author, email, date = header
            commits.append(
                Commit(
                    sha=sha,
                    author=author,
                    email=email,
                    date=date,
                    insertions=ins,
                    deletions=dele,
                )
            )
    return commits
