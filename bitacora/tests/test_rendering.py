from django.test import SimpleTestCase

from bitacora.rendering import render_markdown_to_safe_html


class MarkdownRenderingTests(SimpleTestCase):
    def test_markdown_headings_render_to_html(self):
        html = render_markdown_to_safe_html("# Heading")

        self.assertIn("<h1>Heading</h1>", html)

    def test_fenced_code_blocks_render_safely(self):
        html = render_markdown_to_safe_html("```python\nprint('hi')\n```")

        self.assertIn("<pre>", html)
        self.assertIn("<code", html)
        self.assertIn("print", html)

    def test_unsafe_script_tags_are_removed(self):
        html = render_markdown_to_safe_html("<script>alert('x')</script>")

        self.assertNotIn("<script", html)
        self.assertNotIn("</script>", html)

    def test_raw_javascript_event_handler_attributes_are_not_preserved(self):
        html = render_markdown_to_safe_html('<a href="javascript:alert(1)" onclick="alert(2)">bad</a>')

        self.assertNotIn("javascript:", html)
        self.assertNotIn("onclick", html)
