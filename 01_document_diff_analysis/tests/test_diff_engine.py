"""Tests for document diff engine behavior."""

from __future__ import annotations

from docdiff.diff import diff_documents
from docdiff.model import Document, ParagraphBlock, TableBlock


def test_diff_engine_covers_added_removed_modified_equal() -> None:
    """Diff should classify all four change types deterministically."""
    before = Document(
        source_format="md",
        blocks=[
            ParagraphBlock(block_id="p-0000", index=0, text="anchor start"),
            ParagraphBlock(block_id="p-0001", index=1, text="old text value"),
            ParagraphBlock(block_id="p-0002", index=2, text="remove me"),
            ParagraphBlock(block_id="p-0003", index=3, text="anchor end"),
        ],
    )
    after = Document(
        source_format="md",
        blocks=[
            ParagraphBlock(block_id="p-1000", index=0, text="anchor start"),
            ParagraphBlock(block_id="p-1001", index=1, text="new text value"),
            ParagraphBlock(block_id="p-1002", index=2, text="anchor end"),
            ParagraphBlock(block_id="p-1003", index=3, text="add me"),
        ],
    )

    result = diff_documents(before, after, granularity="block+word")
    changes = [item.change_type for item in result.items]

    assert "equal" in changes
    assert "modified" in changes
    assert "removed" in changes
    assert "added" in changes
    modified_item = next(item for item in result.items if item.change_type == "modified")
    assert any(word.change_type == "removed" for word in modified_item.word_diffs)
    assert any(word.change_type == "added" for word in modified_item.word_diffs)


def test_diff_engine_table_content_diff() -> None:
    """Table modifications should produce modified diff item."""
    before = Document(
        source_format="html",
        blocks=[
            TableBlock(
                block_id="t-0000",
                index=0,
                header=["Name", "Status"],
                rows=[["Parser", "wip"]],
            )
        ],
    )
    after = Document(
        source_format="html",
        blocks=[
            TableBlock(
                block_id="t-1000",
                index=0,
                header=["Name", "Status"],
                rows=[["Parser", "ready"]],
            )
        ],
    )

    result = diff_documents(before, after, granularity="block+word")

    assert len(result.items) == 1
    assert result.items[0].change_type == "modified"
    assert any(token.token == "wip" and token.change_type == "removed" for token in result.items[0].word_diffs)
    assert any(token.token == "ready" and token.change_type == "added" for token in result.items[0].word_diffs)
