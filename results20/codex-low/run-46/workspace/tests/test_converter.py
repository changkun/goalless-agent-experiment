import unittest

from md2html import convert


class TestBlocks(unittest.TestCase):
    def test_heading(self):
        self.assertEqual(convert("# Title"), "<h1>Title</h1>")
        self.assertEqual(convert("### Sub"), "<h3>Sub</h3>")
        self.assertEqual(convert("###### Deep"), "<h6>Deep</h6>")

    def test_paragraph(self):
        self.assertEqual(convert("hello world"), "<p>hello world</p>")

    def test_hard_break(self):
        src = "one\ntwo"
        self.assertEqual(convert(src), "<p>one<br>two</p>")

    def test_hr(self):
        self.assertEqual(convert("---"), "<hr>")

    def test_ul(self):
        src = "- a\n- b"
        self.assertEqual(convert(src), "<ul><li>a</li><li>b</li></ul>")

    def test_ol(self):
        src = "1. a\n2. b"
        self.assertEqual(convert(src), "<ol><li>a</li><li>b</li></ol>")

    def test_blank_line_ends_list(self):
        src = "- a\n- b\n\npara"
        self.assertEqual(
            convert(src),
            "<ul><li>a</li><li>b</li></ul>\n<p>para</p>",
        )

    def test_blockquote(self):
        src = "> one\n> two"
        self.assertEqual(convert(src), "<blockquote><p>one<br>two</p></blockquote>")

    def test_fenced_code(self):
        src = "```python\nprint('x')\n```"
        self.assertEqual(
            convert(src),
            "<pre><code class=\"language-python\">print(&#x27;x&#x27;)</code></pre>",
        )


class TestInline(unittest.TestCase):
    def test_bold(self):
        self.assertEqual(convert("**b**"), "<p><strong>b</strong></p>")

    def test_italic_star(self):
        self.assertEqual(convert("*i*"), "<p><em>i</em></p>")

    def test_italic_underscore(self):
        self.assertEqual(convert("_i_"), "<p><em>i</em></p>")

    def test_code(self):
        self.assertEqual(convert("`x`"), "<p><code>x</code></p>")

    def test_link(self):
        self.assertEqual(
            convert("[t](https://e.com)"),
            '<p><a href="https://e.com">t</a></p>',
        )

    def test_image(self):
        self.assertEqual(
            convert("![alt](img.png)"),
            '<p><img src="img.png" alt="alt"></p>',
        )


class TestSafety(unittest.TestCase):
    def test_escapes_html(self):
        self.assertEqual(convert("<script>"), "<p>&lt;script&gt;</p>")

    def test_escapes_entity_in_link_href(self):
        self.assertEqual(
            convert('[x](https://e.com/?a=1&b=2)'),
            '<p><a href="https://e.com/?a=1&amp;b=2">x</a></p>',
        )


class TestEdge(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(convert(""), "")
        self.assertEqual(convert("\n\n"), "")

    def test_type_error(self):
        with self.assertRaises(TypeError):
            convert(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
