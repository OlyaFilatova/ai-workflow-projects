"""Tests for HTML parser behavior."""

from __future__ import annotations

from docdiff.parsers import parse_html, parse_markdown


def test_html_parser_strips_noise_and_preserves_block_order() -> None:
    """Scripts/styles should be ignored while content order is retained."""
    html = """
    <html>
      <head>
        <style>.x { color: red; }</style>
        <script>console.log('ignore');</script>
      </head>
      <body>
        <h1>Release Plan</h1>
        <p>First paragraph for the report.</p>
        <ul>
          <li>Deterministic output</li>
          <li>Parser boundaries</li>
        </ul>
        <table>
          <tr><th>Module</th><th>Status</th></tr>
          <tr><td>html</td><td>ready</td></tr>
        </table>
      </body>
    </html>
    """

    doc = parse_html(html)

    assert [block.block_type for block in doc.blocks] == ["heading", "paragraph", "list", "table"]
    assert doc.blocks[2].items == ["Deterministic output", "Parser boundaries"]
    assert doc.blocks[3].header == ["Module", "Status"]


def test_html_and_markdown_equivalent_content_shapes_are_aligned() -> None:
    """Equivalent HTML and Markdown content should map to compatible block shape."""
    md = """# Project Snapshot

Stable paragraph content.

- one
- two
"""
    html = """
    <h1>Project Snapshot</h1>
    <p>Stable paragraph content.</p>
    <ul><li>one</li><li>two</li></ul>
    """

    md_doc = parse_markdown(md)
    html_doc = parse_html(html)

    assert [b.block_type for b in md_doc.blocks] == [b.block_type for b in html_doc.blocks]
    assert md_doc.blocks[0].text == html_doc.blocks[0].text
    assert md_doc.blocks[2].items == html_doc.blocks[2].items
