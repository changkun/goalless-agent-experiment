import unittest

from mdx.parser import convert, render_html

LEAD = '<p class="lead">'


class InlineTests(unittest.TestCase):
    def test_bold_italic(self):
        self.assertEqual(
            convert("**bold** and *italic*"),
            f"{LEAD}<strong>bold</strong> and <em>italic</em></p>",
        )

    def test_inline_code(self):
        self.assertEqual(
            convert("Use `x < 1` here"),
            f"{LEAD}Use <code>x &lt; 1</code> here</p>",
        )

    def test_link(self):
        self.assertEqual(
            convert("[text](https://e.com)"),
            f'{LEAD}<a href="https://e.com">text</a></p>',
        )

    def test_link_with_title(self):
        self.assertEqual(
            convert('[text](https://e.com "Title")'),
            f'{LEAD}<a href="https://e.com" title="Title">text</a></p>',
        )

    def test_image(self):
        self.assertEqual(
            convert("![alt](pic.png)"),
            f'{LEAD}<img src="pic.png" alt="alt" /></p>',
        )

    def test_escape_char(self):
        self.assertEqual(convert(r"\*not emphasis\*"), f"{LEAD}*not emphasis*</p>")


class BlockTests(unittest.TestCase):
    def test_heading_levels(self):
        self.assertEqual(convert("# One"), "<h1>One</h1>")
        self.assertEqual(convert("### Three"), "<h3>Three</h3>")

    def test_ul(self):
        self.assertEqual(convert("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")

    def test_ol(self):
        self.assertEqual(convert("1. first\n2. second"), "<ol><li>first</li><li>second</li></ol>")

    def test_code_block_escapes(self):
        self.assertEqual(
            convert("```\nx < 2\n```"),
            "<pre><code>x &lt; 2</code></pre>",
        )

    def test_blockquote(self):
        self.assertEqual(
            convert("> hello"),
            "<blockquote><p>hello</p></blockquote>",
        )

    def test_hr(self):
        self.assertEqual(convert("---"), "<hr />")

    def test_paragraph_wrapping(self):
        self.assertEqual(convert("a\nb"), f"{LEAD}a b</p>")

    def test_first_paragraph_is_lead(self):
        html = convert("hello world\n\nsecond")
        self.assertIn(f"{LEAD}hello world</p>", html)
        self.assertIn("<p>second</p>", html)


class DocumentTests(unittest.TestCase):
    def test_render_html(self):
        doc = render_html("My Title", "<p>hi</p>")
        self.assertIn("<title>My Title</title>", doc)
        self.assertIn("<p>hi</p>", doc)
        self.assertIn("<!DOCTYPE html>", doc)

    def test_render_html_escapes_title(self):
        doc = render_html("Bad <script>", "<p>hi</p>")
        self.assertIn("<title>Bad &lt;script&gt;</title>", doc)
        self.assertNotIn("<script>", doc)


if __name__ == "__main__":
    unittest.main()
