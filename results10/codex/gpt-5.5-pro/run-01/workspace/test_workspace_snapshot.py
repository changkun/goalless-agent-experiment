import json
import tempfile
import unittest
from pathlib import Path

import workspace_snapshot as subject


class WorkspaceSnapshotTests(unittest.TestCase):
    def test_build_snapshot_counts_languages_and_todos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("# TODO: wire config\nprint('ok')\n")
            (root / "notes.md").write_text("plain text\n")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.js").write_text("FIXME ignored\n")

            snapshot = subject.build_snapshot(root, max_files=5, max_todos=5)

            self.assertEqual(snapshot.files, 2)
            self.assertEqual([todo.tag for todo in snapshot.todos], ["TODO"])
            self.assertEqual(snapshot.todos[0].path, "app.py")
            self.assertEqual(
                {item.language: item.files for item in snapshot.languages},
                {"Python": 1, "Markdown": 1},
            )

    def test_hidden_files_are_excluded_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("SECRET=1\n")
            (root / "visible.txt").write_text("hello\n")

            snapshot = subject.build_snapshot(root, max_files=10, max_todos=10)

            self.assertEqual(snapshot.files, 1)
            self.assertEqual(snapshot.largest_files[0].path, "visible.txt")

    def test_todo_scan_ignores_plain_strings_and_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(
                "message = 'TODO: not a comment'\n"
                "pattern = r'FIXME|TODO'\n"
                "# FIXME: real issue\n"
            )
            (root / "README.md").write_text("TODO-like words in prose are ignored.\n")

            snapshot = subject.build_snapshot(root, max_files=10, max_todos=10)

            self.assertEqual(len(snapshot.todos), 1)
            self.assertEqual(snapshot.todos[0].tag, "FIXME")
            self.assertEqual(snapshot.todos[0].text, "real issue")

    def test_json_cli_output_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.rs").write_text("fn main() {}\n")

            args = subject.parse_args([str(root), "--json"])
            snapshot = subject.build_snapshot(
                Path(args.path),
                max_files=args.max_files,
                max_todos=args.max_todos,
                include_hidden=args.include_hidden,
            )
            encoded = json.dumps(subject.asdict(snapshot))

            self.assertEqual(json.loads(encoded)["files"], 1)


if __name__ == "__main__":
    unittest.main()
