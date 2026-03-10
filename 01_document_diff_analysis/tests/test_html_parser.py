"""Tests for HTML parser behavior."""

from __future__ import annotations

from docdiff.model import HeadingBlock, ListBlock, TableBlock
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
    list_block = doc.blocks[2]
    assert isinstance(list_block, ListBlock)
    assert list_block.items == ["Deterministic output", "Parser boundaries"]
    table_block = doc.blocks[3]
    assert isinstance(table_block, TableBlock)
    assert table_block.header == ["Module", "Status"]


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
    md_heading = md_doc.blocks[0]
    html_heading = html_doc.blocks[0]
    assert isinstance(md_heading, HeadingBlock)
    assert isinstance(html_heading, HeadingBlock)
    assert md_heading.text == html_heading.text
    md_list = md_doc.blocks[2]
    html_list = html_doc.blocks[2]
    assert isinstance(md_list, ListBlock)
    assert isinstance(html_list, ListBlock)
    assert md_list.items == html_list.items
