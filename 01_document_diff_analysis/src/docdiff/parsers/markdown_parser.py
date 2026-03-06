"""Markdown parser that converts Markdown content to NDM blocks."""

from __future__ import annotations

import re
from pathlib import Path

from docdiff.model import Document, HeadingBlock, ListBlock, ParagraphBlock, TableBlock

from .common import make_block_id, normalize_text

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_UNORDERED_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_WINDOWS_NEWLINE = "\r\n"
_LEGACY_MAC_NEWLINE = "\r"
_UNIX_NEWLINE = "\n"


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index]
    separator = lines[index + 1]
    return "|" in header and bool(_TABLE_SEP_RE.match(separator))


def _split_table_row(line: str) -> list[str]:
    trimmed = line.strip().strip("|")
    return [normalize_text(cell) for cell in trimmed.split("|")]


def _flush_paragraph_block(
    paragraph_lines: list[str],
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
) -> list[str]:
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
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
    level: int,
    text_value: str,
) -> None:
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
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
) -> int:
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
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
) -> int:
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
    """Parse Markdown text into a normalized document."""
    lines = text.replace(_WINDOWS_NEWLINE, _UNIX_NEWLINE).replace(_LEGACY_MAC_NEWLINE, _UNIX_NEWLINE).split(
        _UNIX_NEWLINE
    )
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock] = []
    paragraph_buffer: list[str] = []
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            i += 1
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            level = len(heading_match.group(1))
            text_value = normalize_text(heading_match.group(2))
            _append_heading_block(blocks, level, text_value)
            i += 1
            continue

        if _is_table_start(lines, i):
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            i = _consume_table_block(lines, i, blocks)
            continue

        unordered_match = _UNORDERED_ITEM_RE.match(raw)
        ordered_match = _ORDERED_ITEM_RE.match(raw)
        if unordered_match or ordered_match:
            paragraph_buffer = _flush_paragraph_block(paragraph_buffer, blocks)
            ordered = bool(ordered_match)
            i = _consume_list_block(lines, i, ordered, blocks)
            continue

        paragraph_buffer.append(line)
        i += 1

    _flush_paragraph_block(paragraph_buffer, blocks)
    return Document(blocks=blocks, source_format="md")


def parse_markdown_file(path: Path) -> Document:
    """Parse a Markdown file from disk into a normalized document."""
    return parse_markdown(path.read_text(encoding="utf-8"))
