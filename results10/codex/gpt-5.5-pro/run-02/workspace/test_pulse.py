from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

import pulse


class PulseTests(unittest.TestCase):
    def test_add_entry_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulse.jsonl"

            entry = pulse.add_entry(path, " Pick boring tech ", ["Backend", "backend"], " reliable ")

            self.assertEqual(entry.entry_id, 1)
            self.assertEqual(entry.text, "Pick boring tech")
            self.assertEqual(entry.tags, ("backend",))
            self.assertEqual(entry.why, "reliable")

            raw = path.read_text(encoding="utf-8").strip()
            payload = json.loads(raw)
            self.assertEqual(payload["id"], 1)
            self.assertEqual(payload["tags"], ["backend"])

    def test_read_entries_reports_bad_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulse.jsonl"
            path.write_text('{"id": 1}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"pulse\.jsonl:1: invalid entry"):
                pulse.read_entries(path)

    def test_run_list_filters_by_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulse.jsonl"
            pulse.add_entry(path, "First", ["scope"], None)
            pulse.add_entry(path, "Second", ["backend"], None)
            stdout = io.StringIO()

            code = pulse.run(["--file", str(path), "list", "--tag", "backend"], stdout=stdout)

            self.assertEqual(code, 0)
            self.assertNotIn("First", stdout.getvalue())
            self.assertIn("Second", stdout.getvalue())

    def test_show_missing_entry_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulse.jsonl"
            stderr = io.StringIO()

            code = pulse.run(["--file", str(path), "show", "99"], stderr=stderr)

            self.assertEqual(code, 1)
            self.assertIn("entry 99 not found", stderr.getvalue())

    def test_export_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulse.jsonl"
            pulse.add_entry(path, "Keep it small", ["scope"], "easier to finish")
            stdout = io.StringIO()

            code = pulse.run(["--file", str(path), "export-md"], stdout=stdout)

            self.assertEqual(code, 0)
            markdown = stdout.getvalue()
            self.assertIn("# Pulse Log", markdown)
            self.assertIn("## 1. Keep it small `#scope`", markdown)
            self.assertIn("- Why: easier to finish", markdown)


if __name__ == "__main__":
    unittest.main()
