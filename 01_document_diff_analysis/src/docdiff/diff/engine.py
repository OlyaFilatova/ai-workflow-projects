"""Deterministic hierarchical diff engine for normalized document models."""

from __future__ import annotations

from difflib import SequenceMatcher
from itertools import zip_longest

from docdiff.model import (
    Block,
    DiffItem,
    DiffResult,
    Document,
    Granularity,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    WordDiff,
)

_TEXTUAL_BLOCKS = (HeadingBlock, ParagraphBlock, ListBlock)


def _block_signature(block: Block) -> tuple[str, str]:
    if isinstance(block, HeadingBlock):
        return (block.block_type, f"{block.level}:{block.text}")
    if isinstance(block, ParagraphBlock):
        return (block.block_type, block.text)
    if isinstance(block, ListBlock):
        return (block.block_type, "|".join(block.items))
    if isinstance(block, TableBlock):
        header = "|".join(block.header or [])
        rows = "||".join("|".join(row) for row in block.rows)
        return (block.block_type, f"{header}::{rows}")
    return (block.block_type, f"{block.source or ''}:{block.alt_text or ''}:{block.caption or ''}")


def _block_text(block: Block) -> str:
    if isinstance(block, HeadingBlock):
        return block.text
    if isinstance(block, ParagraphBlock):
        return block.text
    if isinstance(block, ListBlock):
        return " ".join(block.items)
    if isinstance(block, TableBlock):
        header = " ".join(block.header or [])
        body = " ".join(" ".join(row) for row in block.rows)
        return f"{header} {body}".strip()
    return " ".join(filter(None, [block.alt_text, block.caption, block.source]))


def _word_diff(before_text: str, after_text: str) -> list[WordDiff]:
    before_words = before_text.split()
    after_words = after_text.split()
    matcher = SequenceMatcher(a=before_words, b=after_words, autojunk=False)
    output: list[WordDiff] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            output.extend(WordDiff(token=token, change_type="equal") for token in before_words[i1:i2])
        elif tag == "delete":
            output.extend(WordDiff(token=token, change_type="removed") for token in before_words[i1:i2])
        elif tag == "insert":
            output.extend(WordDiff(token=token, change_type="added") for token in after_words[j1:j2])
        elif tag == "replace":
            output.extend(WordDiff(token=token, change_type="removed") for token in before_words[i1:i2])
            output.extend(WordDiff(token=token, change_type="added") for token in after_words[j1:j2])

    return output


def _build_modified_item(before: Block, after: Block, granularity: Granularity) -> DiffItem:
    include_word_diff = granularity in {"block+word", "word"}
    if include_word_diff and (isinstance(before, _TEXTUAL_BLOCKS) or isinstance(after, _TEXTUAL_BLOCKS)):
        return DiffItem(
            change_type="modified",
            before=before,
            after=after,
            word_diffs=_word_diff(_block_text(before), _block_text(after)),
        )

    if include_word_diff and (isinstance(before, TableBlock) or isinstance(after, TableBlock)):
        return DiffItem(
            change_type="modified",
            before=before,
            after=after,
            word_diffs=_word_diff(_block_text(before), _block_text(after)),
        )

    return DiffItem(change_type="modified", before=before, after=after)


def diff_documents(
    before: Document,
    after: Document,
    granularity: Granularity = "block+word",
) -> DiffResult:
    """Diff two normalized documents using deterministic block alignment."""
    before_signatures = [_block_signature(block) for block in before.blocks]
    after_signatures = [_block_signature(block) for block in after.blocks]

    matcher = SequenceMatcher(a=before_signatures, b=after_signatures, autojunk=False)
    items: list[DiffItem] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for before_block, after_block in zip(before.blocks[i1:i2], after.blocks[j1:j2], strict=True):
                items.append(DiffItem(change_type="equal", before=before_block, after=after_block))
            continue

        if tag == "delete":
            for block in before.blocks[i1:i2]:
                items.append(DiffItem(change_type="removed", before=block, after=None))
            continue

        if tag == "insert":
            for block in after.blocks[j1:j2]:
                items.append(DiffItem(change_type="added", before=None, after=block))
            continue

        if tag == "replace":
            before_slice = before.blocks[i1:i2]
            after_slice = after.blocks[j1:j2]
            for before_block, after_block in zip_longest(before_slice, after_slice):
                if before_block is not None and after_block is not None:
                    items.append(_build_modified_item(before_block, after_block, granularity))
                elif before_block is not None:
                    items.append(DiffItem(change_type="removed", before=before_block, after=None))
                elif after_block is not None:
                    items.append(DiffItem(change_type="added", before=None, after=after_block))

    return DiffResult(granularity=granularity, items=items)
