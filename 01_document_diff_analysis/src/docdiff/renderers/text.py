"""Text renderer for diff output."""

from __future__ import annotations

from docdiff.model import DiffItem, DiffResult


def _block_summary(item: DiffItem) -> str:
    block = item.after if item.after is not None else item.before
    if block is None:
        return "<empty>"

    if block.block_type == "heading":
        return block.text
    if block.block_type == "paragraph":
        return block.text
    if block.block_type == "list":
        return "; ".join(block.items)
    if block.block_type == "table":
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

    def render(self, result: DiffResult) -> str:
        """Render a diff result as a deterministic text report."""
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
    """Convenience function for text rendering."""
    return TextRenderer().render(result)
