"""Text renderer for diff output."""

from __future__ import annotations

from docdiff.model import DiffItem, DiffResult, HeadingBlock, ListBlock, ParagraphBlock, TableBlock


def _block_summary(item: DiffItem) -> str:
    """Build a one-line summary for a diff item.

    Args:
        item: Diff entry containing before/after blocks.
    """
    block = item.after if item.after is not None else item.before
    if block is None:
        return "<empty>"

    if isinstance(block, (HeadingBlock, ParagraphBlock)):
        return block.text
    if isinstance(block, ListBlock):
        return "; ".join(block.items)
    if isinstance(block, TableBlock):
        header = " | ".join(block.header or [])
        body = " || ".join(" | ".join(row) for row in block.rows)
        return f"{header} || {body}" if header or body else "<table>"
    return " ".join(filter(None, [block.alt_text, block.caption, block.source])) or "<image>"


class TextRenderer:
    """Render diff results to deterministic line-oriented text."""

    _MARKERS = {
        "added": "+",
        "removed": "-",
        "modified": "~",
        "equal": "=",
    }
    """Mapping of diff change types to stable text markers."""

    def render(self, result: DiffResult) -> str:
        """Render a diff result as a deterministic text report.

        Args:
            result: Structured diff output.
        """
        lines = [f"granularity: {result.granularity}"]

        for idx, item in enumerate(result.items):
            marker = self._MARKERS[item.change_type]
            summary = _block_summary(item)
            lines.append(f"{marker} [{idx:04d}] {summary}")

            if item.change_type == "modified" and item.word_diffs:
                tokens = " ".join(f"{self._MARKERS[word.change_type]}{word.token}" for word in item.word_diffs)
                lines.append(f"  words: {tokens}")

        return "\n".join(lines)


def render_text(result: DiffResult) -> str:
    """Render a diff result to text through the default renderer.

    Args:
        result: Structured diff output.
    """
    return TextRenderer().render(result)
