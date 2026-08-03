import unittest

import mdgen
from mdgen.parser import ParseError


class InlineTest(unittest.TestCase):
    def test_bold_italic(self):
        out = mdgen.render_markdown("**bold** and *italic*")
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<em>italic</em>", out)

    def test_inline_code(self):
        out = mdgen.render_markdown("use `x < 3` here")
        self.assertIn("<code>x &lt; 3</code>", out)

    def test_link_and_image(self):
        out = mdgen.render_markdown("[text](https://e.com) ![alt](img.png)")
        self.assertIn('<a href="https://e.com">text</a>', out)
        self.assertIn('<img src="img.png" alt="alt" />', out)

    def test_escaping(self):
        out = mdgen.render_markdown("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)


class BlockTest(unittest.TestCase):
    def test_headings(self):
        out = mdgen.render_markdown("# H1\n## H2")
        self.assertIn("<h1>H1</h1>", out)
        self.assertIn("<h2>H2</h2>", out)

    def test_lists(self):
        out = mdgen.render_markdown("- a\n- b\n\n1. x\n2. y")
        self.assertIn("<ul><li>a</li><li>b</li></ul>", out.replace("\n", ""))
        self.assertIn("<ol><li>x</li><li>y</li></ol>", out.replace("\n", ""))

    def test_code_block(self):
        out = mdgen.render_markdown("```python\nprint(1)\n```")
        self.assertIn('<pre><code class="language-python">print(1)</code></pre>', out)

    def test_blockquote(self):
        out = mdgen.render_markdown("> a quote")
        self.assertIn("<blockquote>a quote</blockquote>", out)


class APITest(unittest.TestCase):
    def test_invalid_input(self):
        with self.assertRaises(ParseError):
            mdgen.render_markdown(123)

    def test_full_page(self):
        page = mdgen.render_html("# Title\n\nbody", "My Page")
        self.assertIn("<title>My Page</title>", page)
        self.assertIn("<h1>Title</h1>", page)


if __name__ == "__main__":
    unittest.main()
