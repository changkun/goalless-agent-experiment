"""Tests for orb's pure rendering helpers (no /proc needed)."""
import unittest

import orb


class BarTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(orb.bar(0, 10), " " * 10)

    def test_full(self):
        self.assertEqual(orb.bar(100, 10), "█" * 10)

    def test_clamps_below_and_above(self):
        self.assertEqual(orb.bar(-5, 10), " " * 10)
        self.assertEqual(orb.bar(150, 10), "█" * 10)

    def test_width_zero(self):
        self.assertEqual(orb.bar(50, 0), "")

    def test_always_full_width(self):
        for v in (1, 25, 49.9, 50, 99, 100):
            out = orb.bar(v, 12)
            self.assertEqual(len(out), 12, f"width not preserved for {v=}")
            # final cell is either a partial block char or blank/full
            self.assertIn(out[-1], set(" ▏▎▍▌▋▊▉█"))


class SparklineTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(orb.sparkline([], 10), "")

    def test_all_low(self):
        self.assertEqual(orb.sparkline([0, 0, 0], 5), "   ")

    def test_all_high(self):
        self.assertEqual(orb.sparkline([100, 100], 5), "██")

    def test_truncates_to_width(self):
        out = orb.sparkline([10] * 20, 5)
        self.assertEqual(len(out), 5)

    def test_ascending(self):
        # higher values should not render dimmer than lower values
        lo, hi = orb.sparkline([10, 90], 20), orb.sparkline([90, 10], 20)
        self.assertLessEqual(lo[0], hi[0])


class HumanBytesTests(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(orb.human_bytes(512), "512 B")

    def test_kib(self):
        self.assertEqual(orb.human_bytes(2048), "2.0 KiB")

    def test_mib_gib(self):
        self.assertEqual(orb.human_bytes(3 * 1024 ** 3), "3.0 GiB")

    def test_none(self):
        self.assertEqual(orb.human_bytes(None), "?")


class UptimeTests(unittest.TestCase):
    def test_days(self):
        self.assertEqual(orb.fmt_uptime(90061), "1d 01:01")

    def test_hours(self):
        self.assertEqual(orb.fmt_uptime(3720), "1h 02m")

    def test_minutes(self):
        self.assertEqual(orb.fmt_uptime(85), "1m 25s")


class RenderTests(unittest.TestCase):
    def test_render_contains_header_and_rows(self):
        rows = [orb.Row("CPU", 42.0, "")]
        out = orb.render(rows, [50, 60], 60, "box", "2h 00m", "0.1, 0.2, 0.3")
        self.assertIn("box", out)
        self.assertIn("42.0%", out)
        self.assertIn("CPU history", out)

    def test_row_narrow_width(self):
        row = orb.Row("Memory", 100.0, "1.0 GiB / 1.0 GiB").render(20)
        self.assertLessEqual(len(row), 20)


if __name__ == "__main__":
    unittest.main()
