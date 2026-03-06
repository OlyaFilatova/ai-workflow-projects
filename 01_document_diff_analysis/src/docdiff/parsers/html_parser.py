"""HTML parser that converts HTML content to NDM blocks."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from docdiff.model import Document, HeadingBlock, ListBlock, ParagraphBlock, TableBlock

from .common import make_block_id, normalize_text
from .io import read_utf8_file

_BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"}
_SKIP_ANCESTOR_TAGS = {"table", "ul", "ol"}


def _has_skipped_ancestor(tag: Tag) -> bool:
    """Check whether a tag is nested under a structure parsed elsewhere.

    Args:
        tag: HTML tag being considered as a top-level block.
    """
    parent = tag.parent
    while isinstance(parent, Tag):
        if parent.name in _SKIP_ANCESTOR_TAGS:
            return True
        parent = parent.parent
    return False


def _extract_table(tag: Tag, index: int) -> TableBlock:
    """Build a table block from an HTML table tag.

    Args:
        tag: Table element to parse.
        index: Output block index.
    """
    rows: list[list[str]] = []
    header: list[str] | None = None

    for row in tag.find_all("tr"):
        header_cells = row.find_all("th")
        data_cells = row.find_all("td")
        if header_cells and header is None:
            header = [normalize_text(cell.get_text(" ", strip=True)) for cell in header_cells]
            continue
        if data_cells:
            rows.append([normalize_text(cell.get_text(" ", strip=True)) for cell in data_cells])

    return TableBlock(
        block_id=make_block_id("table", index),
        index=index,
        header=header,
        rows=rows,
    )


def _extract_heading(tag: Tag, index: int) -> HeadingBlock | None:
    """Build a heading block from an HTML heading tag.

    Args:
        tag: Heading element to parse.
        index: Output block index.
    """
    level = int(tag.name[1])
    text_value = normalize_text(tag.get_text(" ", strip=True))
    if not text_value:
        return None
    return HeadingBlock(
        block_id=make_block_id("heading", index),
        index=index,
        level=level,
        text=text_value,
    )


def _extract_paragraph(tag: Tag, index: int) -> ParagraphBlock | None:
    """Build a paragraph block from a paragraph tag.

    Args:
        tag: Paragraph element to parse.
        index: Output block index.
    """
    text_value = normalize_text(tag.get_text(" ", strip=True))
    if not text_value:
        return None
    return ParagraphBlock(
        block_id=make_block_id("paragraph", index),
        index=index,
        text=text_value,
    )


def _extract_list(tag: Tag, index: int) -> ListBlock | None:
    """Build a list block from an ordered or unordered list tag.

    Args:
        tag: List element to parse.
        index: Output block index.
    """
    items: list[str] = []
    for item in tag.find_all("li", recursive=False):
        normalized_item = normalize_text(item.get_text(" ", strip=True))
        if normalized_item:
            items.append(normalized_item)
    if not items:
        return None
    return ListBlock(
        block_id=make_block_id("list", index),
        index=index,
        ordered=tag.name == "ol",
        items=items,
    )


def _extract_block_from_tag(tag: Tag, index: int) -> HeadingBlock | ParagraphBlock | ListBlock | TableBlock | None:
    """Dispatch an HTML tag to its corresponding normalized block parser.

    Args:
        tag: HTML element to parse.
        index: Output block index.
    """
    if tag.name.startswith("h"):
        return _extract_heading(tag, index)
    if tag.name == "p":
        return _extract_paragraph(tag, index)
    if tag.name in {"ul", "ol"}:
        return _extract_list(tag, index)
    if tag.name == "table":
        return _extract_table(tag, index)
    return None


def parse_html(text: str) -> Document:
    """Parse HTML text into a normalized document.

    Args:
        text: Raw HTML content.
    """
    soup = BeautifulSoup(text, "html.parser")

    for noise in soup(["script", "style", "noscript", "template"]):
        noise.decompose()

    root = soup.body if soup.body else soup
    blocks: list[HeadingBlock | ParagraphBlock | ListBlock | TableBlock] = []

    for tag in root.descendants:
        if not isinstance(tag, Tag) or tag.name not in _BLOCK_TAGS:
            continue
        if _has_skipped_ancestor(tag):
            continue

        block_index = len(blocks)
        block = _extract_block_from_tag(tag, block_index)
        if block is not None:
            blocks.append(block)

    return Document(blocks=blocks, source_format="html")


def parse_html_file(path: Path) -> Document:
    """Parse an HTML file from disk into a normalized document.

    Args:
        path: Path to an HTML file.
    """
    return parse_html(read_utf8_file(path, "HTML"))
