"""Tests for md2html.

Run with either:
    python -m unittest discover -s tests
    python -m pytest tests
"""

import unittest

from md2html import convert


class HeadingsTest(unittest.TestCase):
    def test_h1_to_h6(self):
        for level in range(1, 7):
            md = "#" * level + " Title"
            self.assertEqual(convert(md), f"<h{level}>Title</h{level}>\n")

    def test_trailing_hashes_stripped(self):
        self.assertEqual(convert("## Foo ##"), "<h2>Foo</h2>\n")

    def test_inline_in_heading(self):
        self.assertEqual(
            convert("# *Hi*"), "<h1><em>Hi</em></h1>\n"
        )


class ParagraphTest(unittest.TestCase):
    def test_paragraph(self):
        self.assertEqual(
            convert("hello world"), "<p>hello world</p>\n"
        )

    def test_multiline_joined(self):
        self.assertEqual(
            convert("one\ntwo"), "<p>one two</p>\n"
        )


class EmphasisTest(unittest.TestCase):
    def test_em(self):
        self.assertEqual(convert("*x*"), "<p><em>x</em></p>\n")
        self.assertEqual(convert("_x_"), "<p><em>x</em></p>\n")

    def test_strong(self):
        self.assertEqual(convert("**x**"), "<p><strong>x</strong></p>\n")
        self.assertEqual(convert("__x__"), "<p><strong>x</strong></p>\n")

    def test_strong_inside_em(self):
        self.assertEqual(
            convert("***x***"), "<p><strong><em>x</em></strong></p>\n"
        )


class CodeTest(unittest.TestCase):
    def test_inline_code(self):
        self.assertEqual(
            convert("`print(1)`"), "<p><code>print(1)</code></p>\n"
        )

    def test_inline_code_escaped(self):
        self.assertEqual(
            convert("`<b>`"), "<p><code>&lt;b&gt;</code></p>\n"
        )

    def test_fenced_block(self):
        self.assertEqual(
            convert("```\n[[x]]\n```"),
            "<pre><code>[[x]]</code></pre>\n",
        )

    def test_fenced_with_language(self):
        self.assertEqual(
            convert("```python\nx\n```"),
            '<pre><code class="language-python">x</code></pre>\n',
        )

    def test_indented_code(self):
        # 4-space indented code block
        self.assertEqual(
            convert("    x = 1"), "<pre><code>x = 1</code></pre>\n"
        )


class LinkTest(unittest.TestCase):
    def test_link(self):
        self.assertEqual(
            convert("[a](http://x.com)"),
            '<p><a href="http://x.com">a</a></p>\n',
        )

    def test_link_with_title(self):
        self.assertEqual(
            convert('[a](http://x.com "t")'),
            '<p><a href="http://x.com" title="t">a</a></p>\n',
        )

    def test_link_label_inline(self):
        self.assertEqual(
            convert("[*a*](http://x.com)"),
            '<p><a href="http://x.com"><em>a</em></a></p>\n',
        )

    def test_image(self):
        self.assertEqual(
            convert("![alt](img.png)"),
            '<p><img src="img.png" alt="alt"></p>\n',
        )

    def test_autolink(self):
        self.assertEqual(
            convert("see http://x.com now"),
            '<p>see <a href="http://x.com">http://x.com</a> now</p>\n',
        )

    def test_autolink_trailing_period_not_consumed(self):
        self.assertEqual(
            convert("go to http://x.com."),
            '<p>go to <a href="http://x.com">http://x.com</a>.</p>\n',
        )


class QuoteTest(unittest.TestCase):
    def test_blockquote(self):
        self.assertEqual(
            convert("> hi"),
            "<blockquote>\n<p>hi</p>\n</blockquote>\n",
        )

    def test_blockquote_multiline(self):
        self.assertEqual(
            convert("> one\n> two"),
            "<blockquote>\n<p>one two</p>\n</blockquote>\n",
        )


class ListTest(unittest.TestCase):
    def test_unordered(self):
        self.assertEqual(
            convert("- a\n- b"),
            "<ul>\n<li><p>a</p></li>\n<li><p>b</p></li>\n</ul>\n",
        )

    def test_ordered(self):
        self.assertEqual(
            convert("1. a\n2. b"),
            "<ol>\n<li><p>a</p></li>\n<li><p>b</p></li>\n</ol>\n",
        )

    def test_nested(self):
        self.assertEqual(
            convert("- a\n  - b"),
            "<ul>\n<li><p>a</p>\n<ul>\n<li><p>b</p></li>\n</ul></li>\n</ul>\n",
        )


class EscapingTest(unittest.TestCase):
    def test_angle_brackets(self):
        self.assertEqual(
            convert("a < b > c"), "<p>a &lt; b &gt; c</p>\n"
        )

    def test_ampersand(self):
        self.assertEqual(convert("a & b"), "<p>a &amp; b</p>\n")


class HrTest(unittest.TestCase):
    def test_hr(self):
        self.assertEqual(convert("---"), "<hr>\n")
        self.assertEqual(convert("***"), "<hr>\n")
        self.assertEqual(convert("___"), "<hr>\n")


if __name__ == "__main__":
    unittest.main()
