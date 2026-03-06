"""Serialization tests for normalized document and diff models."""

from __future__ import annotations

import json

from docdiff.model import (
    DiffItem,
    DiffResult,
    Document,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    WordDiff,
)


def test_document_to_dict_is_json_serializable() -> None:
    """Document model should serialize deterministically to JSON."""
    doc = Document(
        source_format="md",
        blocks=[
            HeadingBlock(block_id="h-0001", index=0, level=1, text="Release Notes"),
            ParagraphBlock(
                block_id="p-0002",
                index=1,
                text="This sprint includes parser fixes and test hardening.",
            ),
            ListBlock(
                block_id="l-0003",
                index=2,
                ordered=False,
                items=[
                    "Normalize Unicode input",
                    "Stabilize block ordering",
                    "Document known parser limits",
                ],
            ),
            TableBlock(
                block_id="t-0004",
                index=3,
                header=["Module", "Status"],
                rows=[
                    ["markdown", "ready"],
                    ["html", "ready"],
                    ["docx", "planned"],
                ],
            ),
            ParagraphBlock(
                block_id="p-0005",
                index=4,
                text=(
                    "A second paragraph with realistic detail about compatibility "
                    "and deterministic rendering output."
                ),
            ),
        ],
        metadata={"title": "Sprint Report"},
    )

    payload = doc.to_dict()
    dumped = json.dumps(payload, sort_keys=True)

    assert payload["source_format"] == "md"
    assert payload["blocks"][0]["block_id"] == "h-0001"
    assert "deterministic rendering output" in dumped


def test_diff_result_to_dict_is_json_serializable() -> None:
    """Diff result should serialize with block and word-level entries."""
    result = DiffResult(
        granularity="block+word",
        items=[
            DiffItem(
                change_type="equal",
                before=ParagraphBlock(block_id="p-1", index=0, text="Stable text"),
                after=ParagraphBlock(block_id="p-1", index=0, text="Stable text"),
            ),
            DiffItem(
                change_type="modified",
                before=ParagraphBlock(block_id="p-2", index=1, text="Old content"),
                after=ParagraphBlock(block_id="p-2", index=1, text="New content"),
                word_diffs=[
                    WordDiff(token="Old", change_type="removed"),
                    WordDiff(token="New", change_type="added"),
                    WordDiff(token="content", change_type="equal"),
                ],
            ),
        ],
    )

    payload = result.to_dict()
    dumped = json.dumps(payload, sort_keys=True)

    assert payload["granularity"] == "block+word"
    assert payload["items"][1]["word_diffs"][0]["change_type"] == "removed"
    assert "modified" in dumped
