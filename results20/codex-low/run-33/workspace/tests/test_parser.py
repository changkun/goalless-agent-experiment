import unittest

from mdgen.parser import to_html


class ParserTest(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(to_html("# Title"), "<h1>Title</h1>")
        self.assertEqual(to_html("###### Tiny"), "<h6>Tiny</h6>")

    def test_inline_formatting(self):
        md = "This has **bold**, *italic*, and `code`."
        self.assertEqual(
            to_html(md),
            "<p>This has <strong>bold</strong>, <em>italic</em>, and <code>code</code>.</p>",
        )

    def test_link_and_image(self):
        self.assertEqual(
            to_html("[home](https://example.com)"),
            '<p><a href="https://example.com">home</a></p>',
        )
        self.assertEqual(
            to_html("![logo](/img.png)"),
            '<p><img src="/img.png" alt="logo" /></p>',
        )

    def test_unordered_list(self):
        md = "- a\n- b\n- c"
        self.assertEqual(
            to_html(md), "<ul>\n<li>a</li>\n<li>b</li>\n<li>c</li>\n</ul>"
        )

    def test_ordered_list(self):
        md = "1. one\n2. two"
        self.assertEqual(to_html(md), "<ol>\n<li>one</li>\n<li>two</li>\n</ol>")

    def test_fenced_code_block(self):
        md = "```python\nprint('hi')\n```"
        self.assertEqual(
            to_html(md),
            "<pre><code class=\"language-python\">print('hi')</code></pre>",
        )

    def test_blockquote(self):
        self.assertEqual(
            to_html("> beep"), "<blockquote><p>beep</p></blockquote>"
        )

    def test_escaping(self):
        self.assertEqual(
            to_html("2 < 3 & 4 > 1"),
            "<p>2 &lt; 3 &amp; 4 &gt; 1</p>",
        )

    def test_blank_lines_separate_paragraphs(self):
        md = "first\n\nsecond"
        self.assertEqual(to_html(md), "<p>first</p>\n<p>second</p>")


if __name__ == "__main__":
    unittest.main()
