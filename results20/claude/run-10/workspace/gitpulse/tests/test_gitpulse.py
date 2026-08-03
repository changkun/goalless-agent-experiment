"""End-to-end tests for gitpulse using a real throwaway repository.

We build a small git repo in a temporary directory (one shared fixture
for the whole test class, created once per module) and assert against
gitpulse's output. This exercises the full plumbing path: git log parsing,
analysis, and formatting.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gitpulse.analyzer import analyze
from gitpulse.cli import build_parser, main, format_report
from gitpulse.errors import NotAGitRepo
from gitpulse.git import current_branch, is_repo, load_commits

GIT = "git"
ENV = {"GIT_CONFIG_NOSYSTEM": "1", "HOME": tempfile.gettempdir()}


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        [GIT, "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env={**os.environ, **ENV},
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr}"
    return proc.stdout


def commit(repo: Path, author: str, message: str, when: datetime) -> None:
    """Create one commit with a fixed author date."""
    iso = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %z")
    with (repo / "file.txt").open("a") as handle:
        handle.write(f"{message}\n")
    git(repo, "add", "-A")
    env = {**os.environ, **ENV}
    subprocess.run(
        [GIT, "-C", str(repo), "commit", "-m", message, "--author", f"{author} <{author}@example.com>", "--date", iso],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


class GitPulseEndToEnd(unittest.TestCase):
    repo: Path
    created = False

    @classmethod
    def setUpClass(cls) -> None:
        if cls is not GitPulseEndToEnd:
            return
        cls._tmp = tempfile.mkdtemp(prefix="gitpulse-test-")
        cls.repo = Path(cls._tmp) / "fixture"
        cls.repo.mkdir()
        git(cls.repo, "init", "-q", "-b", "main")
        git(cls.repo, "config", "user.name", "Test")
        git(cls.repo, "config", "user.email", "test@example.com")

        base = datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc)
        # Alice: 5 commits across 3 distinct days.
        for i in range(5):
            commit(cls.repo, "Alice", f"alice #{i}", base + timedelta(days=i // 2))
        # Bob: 2 commits on the same day.
        for i in range(2):
            commit(cls.repo, "Bob", f"bob #{i}", base + timedelta(days=3))
        # A merge commit to confirm --no-merges excludes it.
        git(cls.repo, "checkout", "-q", "-b", "feature")
        commit(cls.repo, "Alice", "feature work", base + timedelta(days=4))
        git(cls.repo, "checkout", "-q", "main")
        subprocess.run(
            [GIT, "-C", str(cls.repo), "merge", "--no-ff", "-m", "merge feature", "feature"],
            capture_output=True,
            text=True,
            env={**os.environ, **ENV},
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls is not GitPulseEndToEnd:
            return
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_is_repo(self) -> None:
        self.assertTrue(is_repo(str(self.repo)))
        self.assertFalse(is_repo(self._tmp))

    def test_current_branch(self) -> None:
        self.assertEqual(current_branch(str(self.repo)), "main")

    def test_load_commits_excludes_merges(self) -> None:
        commits = load_commits(str(self.repo))
        # 6 alice (5 on main + 1 feature) + 2 bob = 8; merge commit excluded.
        self.assertEqual(len(commits), 8)

    def test_limit(self) -> None:
        commits = load_commits(str(self.repo), limit=3)
        self.assertEqual(len(commits), 3)

    def test_stats(self) -> None:
        commits = load_commits(str(self.repo))
        stats = analyze(commits, repo_path=str(self.repo), branch="main")
        self.assertEqual(stats.total_commits, 8)
        self.assertEqual(stats.active_days, 5)  # alice: 4, bob: 1
        self.assertEqual(stats.bus_factor, 1)  # Alice alone > 50% of commits
        self.assertEqual(stats.authors["Alice"], 6)
        self.assertEqual(stats.authors["Bob"], 2)
        self.assertAlmostEqual(stats.avg_commits_per_active_day, 8 / 5)

    def test_format_report(self) -> None:
        commits = load_commits(str(self.repo))
        stats = analyze(commits, repo_path=str(self.repo), branch="main")
        report = format_report(stats)
        self.assertIn("Alice", report)
        self.assertIn("Bus factor", report)
        self.assertIn("main", report)

    def test_cli_main_returns_zero(self) -> None:
        self.assertEqual(main([str(self.repo)]), 0)

    def test_cli_rejects_non_repo(self) -> None:
        # main() returns 1 and prints to stderr; capture to avoid noise.
        import io
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main([self._tmp])
        self.assertEqual(code, 1)
        self.assertIn("not inside a git working tree", err.getvalue())

    def test_not_a_git_repo_raised(self) -> None:
        with self.assertRaises(NotAGitRepo):
            load_commits(self._tmp)

    def test_parser(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--limit", "5"])
        self.assertEqual(args.limit, 5)


if __name__ == "__main__":
    unittest.main()
