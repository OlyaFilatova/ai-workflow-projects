"""Markdown parser that converts Markdown content to NDM blocks."""

from __future__ import annotations

import re
from pathlib import Path

from docdiff.model import Block, Document, HeadingBlock, ListBlock, ParagraphBlock, TableBlock

from .common import make_block_id, normalize_text
from .io import read_utf8_file

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_UNORDERED_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_WINDOWS_NEWLINE = "\r\n"
_LEGACY_MAC_NEWLINE = "\r"
_UNIX_NEWLINE = "\n"


def _is_table_start(lines: list[str], index: int) -> bool:
    """Determine whether a markdown table starts at a given line.

    Args:
        lines: Source markdown split into lines.
        index: Candidate header-line index.
    """
    if index + 1 >= len(lines):
        return False
    header = lines[index]
    separator = lines[index + 1]
    return "|" in header and bool(_TABLE_SEP_RE.match(separator))


def _split_table_row(line: str) -> list[str]:
    """Split a markdown table row into normalized cells.

    Args:
        line: Raw markdown table row.
    """
    trimmed = line.strip().strip("|")
    return [normalize_text(cell) for cell in trimmed.split("|")]


def _flush_paragraph_block(
    paragraph_lines: list[str],
    blocks: list[Block],
) -> list[str]:
    """Emit a buffered paragraph block and clear its line buffer.

    Args:
        paragraph_lines: Buffered paragraph lines.
        blocks: Accumulated output block list.
    """
    if not paragraph_lines:
        return []
    paragraph_text = normalize_text(" ".join(paragraph_lines))
    if paragraph_text:
        index = len(blocks)
        blocks.append(
            ParagraphBlock(
                block_id=make_block_id("paragraph", index),
                index=index,
                text=paragraph_text,
            )
        )
    return []


def _append_heading_block(
    blocks: list[Block],
    level: int,
    text_value: str,
) -> None:
    """Append a normalized heading block to the output sequence.

    Args:
        blocks: Accumulated output block list.
        level: Heading level between 1 and 6.
        text_value: Normalized heading text.
    """
    index = len(blocks)
    blocks.append(
        HeadingBlock(
            block_id=make_block_id("heading", index),
            index=index,
            level=level,
            text=text_value,
        )
    )


def _consume_table_block(
    lines: list[str],
    start_index: int,
    blocks: list[Block],
) -> int:
    """Parse a markdown table and append it as one block.

    Args:
        lines: Source markdown split into lines.
        start_index: Table header line index.
        blocks: Accumulated output block list.
    """
    header = _split_table_row(lines[start_index])
    next_index = start_index + 2
    rows: list[list[str]] = []
    while next_index < len(lines) and "|" in lines[next_index] and lines[next_index].strip():
        rows.append(_split_table_row(lines[next_index]))
        next_index += 1
    index = len(blocks)
    blocks.append(
        TableBlock(
            block_id=make_block_id("table", index),
            index=index,
            header=header,
            rows=rows,
        )
    )
    return next_index


def _consume_list_block(
    lines: list[str],
    start_index: int,
    ordered: bool,
    blocks: list[Block],
) -> int:
    """Parse a contiguous markdown list and append it as one block.

    Args:
        lines: Source markdown split into lines.
        start_index: First list-item line index.
        ordered: Whether list markers are ordered.
        blocks: Accumulated output block list.
    """
    items: list[str] = []
    next_index = start_index
    while next_index < len(lines):
        current_line = lines[next_index]
        unordered_match = _UNORDERED_ITEM_RE.match(current_line)
        ordered_match = _ORDERED_ITEM_RE.match(current_line)
        if ordered and ordered_match:
            items.append(normalize_text(ordered_match.group(1)))
            next_index += 1
            continue
        if not ordered and unordered_match:
            items.append(normalize_text(unordered_match.group(1)))
            next_index += 1
            continue
        break

    index = len(blocks)
    blocks.append(
        ListBlock(
            block_id=make_block_id("list", index),
            index=index,
            ordered=ordered,
            items=items,
        )
    )
    return next_index


def parse_markdown(text: str) -> Document:
    """Parse Markdown text into a normalized document.

    Args:
        text: Raw markdown content.
    """
    lines = text.replace(_WINDOWS_NEWLINE, _UNIX_NEWLINE).replace(_LEGACY_MAC_NEWLINE, _UNIX_NEWLINE).split(
        _UNIX_NEWLINE
    )
    blocks: list[Block] = []
    paragraph_buffer: list[str] = []
    line_index = 0

    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped_line = raw_line.strip()

        if not stripped_line:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            line_index += 1
            continue

        heading_match = _HEADING_RE.match(stripped_line)
        if heading_match:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            level = len(heading_match.group(1))
            text_value = normalize_text(heading_match.group(2))
            _append_heading_block(blocks, level, text_value)
            line_index += 1
            continue

        if _is_table_start(lines, line_index):
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            line_index = _consume_table_block(lines, line_index, blocks)
            continue

        unordered_match = _UNORDERED_ITEM_RE.match(raw_line)
        ordered_match = _ORDERED_ITEM_RE.match(raw_line)
        if unordered_match or ordered_match:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            ordered = bool(ordered_match)
            line_index = _consume_list_block(lines, line_index, ordered, blocks)
            continue

        paragraph_buffer.append(stripped_line)
        line_index += 1

    _flush_paragraph_block(paragraph_buffer, blocks)
    return Document(blocks=blocks, source_format="md")


def parse_markdown_file(path: Path) -> Document:
    """Parse a Markdown file from disk into a normalized document.

    Args:
        path: Path to a markdown file.
    """
    return parse_markdown(read_utf8_file(path, "Markdown"))
