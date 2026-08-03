import unittest

from pagepress.md import markdown, extract_title


class ExtractTitleTest(unittest.TestCase):
    def test_first_h1(self):
        self.assertEqual(extract_title("# Hello\n\nSome text"), "Hello")

    def test_skips_h2_and_returns_none(self):
        self.assertIsNone(extract_title("## Not an h1"))


class MarkdownTest(unittest.TestCase):
    def test_heading(self):
        self.assertEqual(markdown("# Title"), "<h1>Title</h1>")

    def test_paragraph(self):
        self.assertEqual(markdown("hello world"), "<p>hello world</p>")

    def test_bold_and_emphasis(self):
        self.assertEqual(markdown("**b** and *i*"), "<p><strong>b</strong> and <em>i</em></p>")

    def test_inline_code(self):
        self.assertEqual(markdown("use `x = 1`"), "<p>use <code>x = 1</code></p>")

    def test_links(self):
        self.assertEqual(
            markdown("[text](https://a.b)"), '<p><a href="https://a.b">text</a></p>'
        )

    def test_fenced_code_with_language(self):
        html = markdown("```python\nprint('hi')\n```")
        self.assertIn('<pre><code class="language-python">', html)
        self.assertIn("hi", html)

    def test_ul(self):
        html = markdown("- a\n- b")
        self.assertEqual(html, "<ul><li>a</li><li>b</li></ul>")

    def test_ol(self):
        html = markdown("1. first\n2. second")
        self.assertEqual(html, "<ol><li>first</li><li>second</li></ol>")

    def test_blockquote(self):
        self.assertEqual(markdown("> quoted"), "<blockquote>quoted</blockquote>")

    def test_hr(self):
        self.assertEqual(markdown("---"), "<hr>")

    def test_escaping_html(self):
        self.assertEqual(markdown("<script>alert(1)</script>"), "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>")


if __name__ == "__main__":
    unittest.main()
