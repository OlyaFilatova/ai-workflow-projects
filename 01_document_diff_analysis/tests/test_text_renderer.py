"""Tests for text renderer output."""

from __future__ import annotations

from docdiff.model import DiffItem, DiffResult, ParagraphBlock, WordDiff
from docdiff.renderers import TextRenderer


def test_text_renderer_covers_all_change_markers() -> None:
    """Renderer output should include markers for all change types."""
    result = DiffResult(
        granularity="block+word",
        items=[
            DiffItem(
                change_type="equal",
                before=ParagraphBlock(block_id="p-0", index=0, text="same"),
                after=ParagraphBlock(block_id="p-0", index=0, text="same"),
            ),
            DiffItem(
                change_type="removed",
                before=ParagraphBlock(block_id="p-1", index=1, text="removed text"),
            ),
            DiffItem(
                change_type="added",
                after=ParagraphBlock(block_id="p-2", index=2, text="added text"),
            ),
            DiffItem(
                change_type="modified",
                before=ParagraphBlock(block_id="p-3", index=3, text="old text"),
                after=ParagraphBlock(block_id="p-3", index=3, text="new text"),
                word_diffs=[
                    WordDiff(token="old", change_type="removed"),
                    WordDiff(token="new", change_type="added"),
                    WordDiff(token="text", change_type="equal"),
                ],
            ),
        ],
    )

    rendered = TextRenderer().render(result)

    assert "granularity: block+word" in rendered
    assert "= [0000] same" in rendered
    assert "- [0001] removed text" in rendered
    assert "+ [0002] added text" in rendered
    assert "~ [0003] new text" in rendered
    assert "words: -old +new =text" in rendered
