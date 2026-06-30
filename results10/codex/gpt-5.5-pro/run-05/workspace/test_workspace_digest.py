from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from workspace_digest import render_markdown, scan_tree


class WorkspaceDigestTests(unittest.TestCase):
    def test_scan_tree_counts_files_and_skips_default_ignored_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (root / "README").write_text("plain name\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "leftpad.js").write_text("module.exports = 1\n", encoding="utf-8")

            digest = scan_tree(root)
            paths = {file.path.as_posix() for file in digest.files}

            self.assertEqual(paths, {"README", "app.py", "docs/guide.md"})
            self.assertEqual(digest.directories, 1)
            self.assertEqual([path.as_posix() for path in digest.skipped_dirs], ["node_modules"])
            self.assertEqual(digest.extension_counts[".py"], 1)
            self.assertEqual(digest.extension_counts[".md"], 1)
            self.assertEqual(digest.extension_counts["[none]"], 1)

    def test_render_markdown_orders_file_types_by_size(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "small.py").write_text("x\n", encoding="utf-8")
            (root / "large.txt").write_text("x" * 2048, encoding="utf-8")

            markdown = render_markdown(scan_tree(root), top=1, file_limit=1)

            self.assertIn("# Workspace Digest:", markdown)
            self.assertIn("| `.txt` | 1 | 2.0 KiB |", markdown)
            self.assertIn("| `large.txt` | 2.0 KiB |", markdown)
            self.assertIn("... 1 more", markdown)


if __name__ == "__main__":
    unittest.main()
