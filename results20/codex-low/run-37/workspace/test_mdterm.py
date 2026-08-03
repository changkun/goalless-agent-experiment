import unittest

from mdterm import render, NO_COLOR, FULL_COLOR


class RenderTests(unittest.TestCase):
    def test_heading(self):
        out = render("# Hello", NO_COLOR)
        self.assertIn("Hello", out)

    def test_fenced_code(self):
        src = "```python\nprint(1)\n```"
        out = render(src, NO_COLOR)
        self.assertIn("print(1)", out)
        colored = render(src, FULL_COLOR)
        self.assertIn("python", colored)

    def test_list(self):
        out = render("- one\n- two", NO_COLOR)
        self.assertIn("- one", out)
        self.assertIn("- two", out)

    def test_link_stripped_in_plain(self):
        out = render("see [OpenAI](https://openai.com)", NO_COLOR)
        self.assertIn("see OpenAI", out)
        self.assertNotIn("https://openai.com", out)

    def test_inline_code_stripped_in_plain(self):
        out = render("run `make test` now", NO_COLOR)
        self.assertIn("run make test now", out)
        self.assertNotIn("`", out)

    def test_link_colored_in_full(self):
        out = render("[OpenAI](https://openai.com)", FULL_COLOR)
        self.assertIn("\x1b[", out)
        self.assertIn("https://openai.com", out)

    def test_blockquote(self):
        out = render("> hello there", NO_COLOR)
        self.assertIn("hello there", out)

    def test_horizontal_rule(self):
        out = render("---", NO_COLOR)
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
