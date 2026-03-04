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


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index]
    separator = lines[index + 1]
    return "|" in header and bool(_TABLE_SEP_RE.match(separator))


def _split_table_row(line: str) -> list[str]:
    trimmed = line.strip().strip("|")
    return [normalize_text(cell) for cell in trimmed.split("|")]


def parse_markdown(text: str) -> Document:
    """Parse Markdown text into a normalized document."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock] = []
    paragraph_buffer: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        if not paragraph_buffer:
            return
        paragraph_text = normalize_text(" ".join(paragraph_buffer))
        if paragraph_text:
            index = len(blocks)
            blocks.append(
                ParagraphBlock(
                    block_id=make_block_id("paragraph", index),
                    index=index,
                    text=paragraph_text,
                )
            )
        paragraph_buffer = []

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            flush_paragraph()
            i += 1
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            text_value = normalize_text(heading_match.group(2))
            index = len(blocks)
            blocks.append(
                HeadingBlock(
                    block_id=make_block_id("heading", index),
                    index=index,
                    level=level,
                    text=text_value,
                )
            )
            i += 1
            continue

        if _is_table_start(lines, i):
            flush_paragraph()
            header = _split_table_row(lines[i])
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_split_table_row(lines[i]))
                i += 1
            index = len(blocks)
            blocks.append(
                TableBlock(
                    block_id=make_block_id("table", index),
                    index=index,
                    header=header,
                    rows=rows,
                )
            )
            continue

        unordered_match = _UNORDERED_ITEM_RE.match(raw)
        ordered_match = _ORDERED_ITEM_RE.match(raw)
        if unordered_match or ordered_match:
            flush_paragraph()
            ordered = bool(ordered_match)
            items: list[str] = []
            while i < len(lines):
                current_raw = lines[i]
                um = _UNORDERED_ITEM_RE.match(current_raw)
                om = _ORDERED_ITEM_RE.match(current_raw)
                if ordered and om:
                    items.append(normalize_text(om.group(1)))
                    i += 1
                    continue
                if not ordered and um:
                    items.append(normalize_text(um.group(1)))
                    i += 1
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
            continue

        paragraph_buffer.append(line)
        i += 1

    flush_paragraph()
    return Document(blocks=blocks, source_format="md")


def parse_markdown_file(path: Path) -> Document:
    """Parse a Markdown file from disk into a normalized document."""
    return parse_markdown(path.read_text(encoding="utf-8"))
