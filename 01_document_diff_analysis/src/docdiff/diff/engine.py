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
_LIST_ITEM_SEPARATOR = "|"
_TABLE_HEADER_SEPARATOR = "|"
_TABLE_ROW_SEPARATOR = "||"
_TABLE_SECTION_SEPARATOR = "::"
_TEXT_PART_SEPARATOR = " "
_WORD_DIFF_EQUAL = "equal"
_WORD_DIFF_ADDED = "added"
_WORD_DIFF_REMOVED = "removed"
_CHANGE_EQUAL = "equal"
_CHANGE_ADDED = "added"
_CHANGE_REMOVED = "removed"
_CHANGE_MODIFIED = "modified"
_OPCODE_EQUAL = "equal"
_OPCODE_DELETE = "delete"
_OPCODE_INSERT = "insert"
_OPCODE_REPLACE = "replace"


def _block_signature(block: Block) -> tuple[str, str]:
    if isinstance(block, HeadingBlock):
        return (block.block_type, f"{block.level}:{block.text}")
    if isinstance(block, ParagraphBlock):
        return (block.block_type, block.text)
    if isinstance(block, ListBlock):
        return (block.block_type, _LIST_ITEM_SEPARATOR.join(block.items))
    if isinstance(block, TableBlock):
        header = _TABLE_HEADER_SEPARATOR.join(block.header or [])
        rows = _TABLE_ROW_SEPARATOR.join(_TABLE_HEADER_SEPARATOR.join(row) for row in block.rows)
        return (block.block_type, f"{header}{_TABLE_SECTION_SEPARATOR}{rows}")
    return (block.block_type, f"{block.source or ''}:{block.alt_text or ''}:{block.caption or ''}")


def _block_text(block: Block) -> str:
    if isinstance(block, HeadingBlock):
        return block.text
    if isinstance(block, ParagraphBlock):
        return block.text
    if isinstance(block, ListBlock):
        return _TEXT_PART_SEPARATOR.join(block.items)
    if isinstance(block, TableBlock):
        header = _TEXT_PART_SEPARATOR.join(block.header or [])
        body = _TEXT_PART_SEPARATOR.join(_TEXT_PART_SEPARATOR.join(row) for row in block.rows)
        return f"{header} {body}".strip()
    return _TEXT_PART_SEPARATOR.join(filter(None, [block.alt_text, block.caption, block.source]))


def _word_diff(before_text: str, after_text: str) -> list[WordDiff]:
    before_words = before_text.split()
    after_words = after_text.split()
    matcher = SequenceMatcher(a=before_words, b=after_words, autojunk=False)
    output: list[WordDiff] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == _OPCODE_EQUAL:
            output.extend(WordDiff(token=token, change_type=_WORD_DIFF_EQUAL) for token in before_words[i1:i2])
        elif tag == _OPCODE_DELETE:
            output.extend(WordDiff(token=token, change_type=_WORD_DIFF_REMOVED) for token in before_words[i1:i2])
        elif tag == _OPCODE_INSERT:
            output.extend(WordDiff(token=token, change_type=_WORD_DIFF_ADDED) for token in after_words[j1:j2])
        elif tag == _OPCODE_REPLACE:
            output.extend(WordDiff(token=token, change_type=_WORD_DIFF_REMOVED) for token in before_words[i1:i2])
            output.extend(WordDiff(token=token, change_type=_WORD_DIFF_ADDED) for token in after_words[j1:j2])

    return output


def _build_modified_item(before: Block, after: Block, granularity: Granularity) -> DiffItem:
    include_word_diff = granularity in {"block+word", "word"}
    if include_word_diff and (isinstance(before, _TEXTUAL_BLOCKS) or isinstance(after, _TEXTUAL_BLOCKS)):
        return DiffItem(
            change_type=_CHANGE_MODIFIED,
            before=before,
            after=after,
            word_diffs=_word_diff(_block_text(before), _block_text(after)),
        )

    if include_word_diff and (isinstance(before, TableBlock) or isinstance(after, TableBlock)):
        return DiffItem(
            change_type=_CHANGE_MODIFIED,
            before=before,
            after=after,
            word_diffs=_word_diff(_block_text(before), _block_text(after)),
        )

    return DiffItem(change_type=_CHANGE_MODIFIED, before=before, after=after)


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
        if tag == _OPCODE_EQUAL:
            for before_block, after_block in zip(before.blocks[i1:i2], after.blocks[j1:j2], strict=True):
                items.append(DiffItem(change_type=_CHANGE_EQUAL, before=before_block, after=after_block))
            continue

        if tag == _OPCODE_DELETE:
            for block in before.blocks[i1:i2]:
                items.append(DiffItem(change_type=_CHANGE_REMOVED, before=block, after=None))
            continue

        if tag == _OPCODE_INSERT:
            for block in after.blocks[j1:j2]:
                items.append(DiffItem(change_type=_CHANGE_ADDED, before=None, after=block))
            continue

        if tag == _OPCODE_REPLACE:
            before_slice = before.blocks[i1:i2]
            after_slice = after.blocks[j1:j2]
            for before_block, after_block in zip_longest(before_slice, after_slice):
                if before_block is not None and after_block is not None:
                    items.append(_build_modified_item(before_block, after_block, granularity))
                elif before_block is not None:
                    items.append(DiffItem(change_type=_CHANGE_REMOVED, before=before_block, after=None))
                elif after_block is not None:
                    items.append(DiffItem(change_type=_CHANGE_ADDED, before=None, after=after_block))

    return DiffResult(granularity=granularity, items=items)
