import unittest

from md2html import convert


class ConvertTest(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(convert("# Hello"), "<h1>Hello</h1>")
        self.assertEqual(convert("###### deep"), "<h6>deep</h6>")

    def test_paragraph(self):
        self.assertEqual(convert("just text"), "<p>just text</p>")

    def test_unordered_list(self):
        md = "- one\n- two"
        self.assertEqual(convert(md), "<ul>\n<li>one</li>\n<li>two</li>\n</ul>")

    def test_ordered_list(self):
        md = "1. first\n2. second"
        self.assertEqual(convert(md), "<ol>\n<li>first</li>\n<li>second</li>\n</ol>")

    def test_code_block(self):
        md = "```python\nprint('hi')\n```"
        self.assertEqual(
            convert(md),
            '<pre><code class="language-python">print(&#x27;hi&#x27;)</code></pre>',
        )

    def test_blockquote(self):
        self.assertEqual(convert("> cite"), "<blockquote><p>cite</p></blockquote>")

    def test_inline(self):
        md = "**bold** and *em* and `code` and [link](https://x.dev)"
        self.assertEqual(
            convert(md),
            '<p><strong>bold</strong> and <em>em</em> and <code>code</code> '
            'and <a href="https://x.dev">link</a></p>',
        )

    def test_html_escaped_in_text(self):
        self.assertEqual(convert("a < b"), "<p>a &lt; b</p>")

    def test_empty(self):
        self.assertEqual(convert(""), "")
        self.assertEqual(convert(None), "")


if __name__ == "__main__":
    unittest.main()
