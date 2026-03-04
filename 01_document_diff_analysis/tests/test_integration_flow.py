"""Integration and cross-format tests."""

from __future__ import annotations

from docdiff.diff import diff_documents
from docdiff.parsers import parse_html, parse_markdown
from docdiff.renderers import render_text


def test_end_to_end_markdown_change_flow() -> None:
    """Parsing, diffing, and rendering should work together deterministically."""
    before_md = """# Release Summary

Parser status is in progress.

- markdown parser
- html parser
"""
    after_md = """# Release Summary

Parser status is ready.

- markdown parser
- html parser
- docx parser
"""

    before = parse_markdown(before_md)
    after = parse_markdown(after_md)
    result = diff_documents(before, after, granularity="block+word")

    rendered_once = render_text(result)
    rendered_twice = render_text(result)

    assert rendered_once == rendered_twice
    assert "~" in rendered_once
    assert "+" in rendered_once


def test_cross_format_markdown_html_equivalence() -> None:
    """Equivalent Markdown and HTML should diff to all-equal blocks."""
    markdown = """# Platform Notes

Stable paragraph for comparison.

- one
- two
"""
    html = """
    <h1>Platform Notes</h1>
    <p>Stable paragraph for comparison.</p>
    <ul><li>one</li><li>two</li></ul>
    """

    md_doc = parse_markdown(markdown)
    html_doc = parse_html(html)
    diff = diff_documents(md_doc, html_doc, granularity="block")

    assert all(item.change_type == "equal" for item in diff.items)
    assert len(diff.items) == 3
