"""Markdown rendering and sanitization helpers."""

import bleach
import markdown


ALLOWED_TAGS = [
    "a",
    "blockquote",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "code": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown_to_safe_html(markdown_text):
    rendered = markdown.markdown(
        markdown_text or "",
        extensions=["fenced_code", "tables"],
    )
    return bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
