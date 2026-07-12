"""Tests for mandelbrot.py — runs without numpy/Pillow."""
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import mandelbrot as m


class TestMandelbrot(unittest.TestCase):
    def test_render_shape(self):
        rows = m.render(m.View(), width=20, height=10)
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(len(r), 20)
            for ch in r:
                self.assertIn(ch, m.PALETTE)

    def test_known_points(self):
        # The origin is inside the set -> should render with PALETTE[0] at centre
        rows = m.render(m.View(cx=0.0, cy=0.0, span=2.5), width=31, height=31)
        self.assertEqual(rows[15][15], m.PALETTE[0])
        # A clearly-divergent point (2,0) escapes at iteration 1
        rows = m.render(m.View(cx=2.0, cy=0.0, span=0.1, max_iter=50), width=21, height=21)
        centre = rows[10][10]
        self.assertNotEqual(centre, m.PALETTE[0])

    def test_zoom_changes_view(self):
        a = m.render(m.View(span=3.0), width=30, height=15)
        b = m.render(m.View(span=0.1), width=30, height=15)
        self.assertNotEqual(a, b)

    def test_ppm_export(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.ppm")
            m.save_image(path, m.View(max_iter=50), 32, 16)
            # Save_image falls back to .ppm if Pillow missing
            produced = os.path.join(d, "out.ppm")
            self.assertTrue(os.path.exists(produced), f"missing {produced}")
            with open(produced, "rb") as f:
                head = f.read(3)
            self.assertTrue(head.startswith(b"P6\n"), head)
            # Header: "P6\n{width} {height}\n255\n" + width*height*3 bytes
            size = os.path.getsize(produced)
            self.assertGreater(size, 3 + 32 * 16 * 3)

    def test_ascii_printable(self):
        rows = m.render(m.View(max_iter=80), 40, 20)
        joined = "\n".join(rows)
        self.assertGreater(len(joined.strip()), 0)
        # Should contain at least one non-space char (the boundary) eventually.
        self.assertTrue(any(c != m.PALETTE[0] for r in rows for c in r))


if __name__ == "__main__":
    unittest.main(verbosity=2)
