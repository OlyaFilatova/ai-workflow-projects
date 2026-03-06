"""Tests for Markdown parser behavior."""

from __future__ import annotations

from docdiff.model import ListBlock, TableBlock
from docdiff.parsers import parse_markdown


def test_markdown_parser_handles_mixed_blocks() -> None:
    """Parser should preserve order across heading, paragraphs, lists, and tables."""
    content = """# Release Plan

This release prepares a stable API surface.
It also improves deterministic behavior.

- Normalize whitespace
- Keep predictable block IDs

| Module | Status |
| ------ | ------ |
| model  | ready  |
| parser | wip    |

Final notes paragraph with extra detail.
"""

    doc = parse_markdown(content)

    assert [block.block_type for block in doc.blocks] == [
        "heading",
        "paragraph",
        "list",
        "table",
        "paragraph",
    ]
    assert doc.blocks[0].block_id == "heading-0000"
    list_block = doc.blocks[2]
    assert isinstance(list_block, ListBlock)
    assert list_block.items == ["Normalize whitespace", "Keep predictable block IDs"]
    table_block = doc.blocks[3]
    assert isinstance(table_block, TableBlock)
    assert table_block.header == ["Module", "Status"]


def test_markdown_parser_supports_ordered_lists() -> None:
    """Ordered list markers should produce ordered list block."""
    doc = parse_markdown(
        """1. first item
2) second item

Trailing paragraph.
"""
    )

    first_block = doc.blocks[0]
    assert first_block.block_type == "list"
    assert isinstance(first_block, ListBlock)
    assert first_block.ordered is True
    assert first_block.items == ["first item", "second item"]
    assert doc.blocks[1].block_type == "paragraph"
