"""DOCX parser that converts DOCX content to NDM blocks."""

from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocumentFactory
from docx.document import Document as DocxDocumentType
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from docdiff.model import Document, HeadingBlock, ListBlock, ParagraphBlock, TableBlock

from .common import make_block_id, normalize_text


def _heading_level(paragraph: DocxParagraph) -> int | None:
    style_name = paragraph.style.name if paragraph.style is not None else ""
    if not style_name.startswith("Heading"):
        return None
    parts = style_name.split()
    if len(parts) < 2:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _is_list_paragraph(paragraph: DocxParagraph) -> tuple[bool, bool]:
    style_name = (paragraph.style.name if paragraph.style is not None else "").lower()
    if "list" not in style_name:
        return (False, False)
    ordered = "number" in style_name
    return (True, ordered)


def _extract_table(table: DocxTable, index: int) -> TableBlock:
    rows: list[list[str]] = []
    for row in table.rows:
        rows.append([normalize_text(cell.text) for cell in row.cells])

    header: list[str] | None = None
    body_rows = rows
    if rows:
        header = rows[0]
        body_rows = rows[1:] if len(rows) > 1 else []

    return TableBlock(
        block_id=make_block_id("table", index),
        index=index,
        header=header,
        rows=body_rows,
    )


def _flush_list_block(
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
    list_items: list[str],
    is_ordered: bool | None,
) -> tuple[list[str], bool | None]:
    if not list_items:
        return ([], None)
    index = len(blocks)
    blocks.append(
        ListBlock(
            block_id=make_block_id("list", index),
            index=index,
            ordered=bool(is_ordered),
            items=list_items,
        )
    )
    return ([], None)


def _append_heading_block(
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
    level: int,
    text: str,
) -> None:
    index = len(blocks)
    blocks.append(
        HeadingBlock(
            block_id=make_block_id("heading", index),
            index=index,
            level=level,
            text=text,
        )
    )


def _append_paragraph_block(
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
    text: str,
) -> None:
    index = len(blocks)
    blocks.append(
        ParagraphBlock(
            block_id=make_block_id("paragraph", index),
            index=index,
            text=text,
        )
    )


def _handle_paragraph(
    paragraph: DocxParagraph,
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock],
    list_buffer: list[str],
    list_ordered: bool | None,
) -> tuple[list[str], bool | None]:
    text = normalize_text(paragraph.text)
    if not text:
        return _flush_list_block(blocks, list_buffer, list_ordered)

    level = _heading_level(paragraph)
    is_list, ordered = _is_list_paragraph(paragraph)

    if level is not None:
        list_buffer, list_ordered = _flush_list_block(blocks, list_buffer, list_ordered)
        _append_heading_block(blocks, level, text)
        return (list_buffer, list_ordered)

    if not is_list:
        list_buffer, list_ordered = _flush_list_block(blocks, list_buffer, list_ordered)
        _append_paragraph_block(blocks, text)
        return (list_buffer, list_ordered)

    if list_ordered is None:
        list_ordered = ordered
    if list_ordered != ordered:
        list_buffer, list_ordered = _flush_list_block(blocks, list_buffer, list_ordered)
        list_ordered = ordered
    list_buffer.append(text)
    return (list_buffer, list_ordered)


def parse_docx_file(path: Path) -> Document:
    """Parse a DOCX file from disk into a normalized document."""
    try:
        docx_doc = DocxDocumentFactory(path)
    except OSError as exc:
        raise OSError(f"Unable to read DOCX file '{path}': {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Unable to parse DOCX file '{path}': {exc}") from exc
    return _parse_docx_document(docx_doc)


def _parse_docx_document(docx_doc: DocxDocumentType) -> Document:
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock] = []
    body = docx_doc.element.body
    list_buffer: list[str] = []
    list_ordered: bool | None = None

    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = DocxParagraph(child, docx_doc)
            list_buffer, list_ordered = _handle_paragraph(paragraph, blocks, list_buffer, list_ordered)
            continue

        if tag == "tbl":
            list_buffer, list_ordered = _flush_list_block(blocks, list_buffer, list_ordered)
            table = DocxTable(child, docx_doc)
            index = len(blocks)
            blocks.append(_extract_table(table, index))

    _flush_list_block(blocks, list_buffer, list_ordered)
    return Document(blocks=blocks, source_format="docx")
