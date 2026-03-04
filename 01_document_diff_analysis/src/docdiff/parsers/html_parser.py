"""HTML parser that converts HTML content to NDM blocks."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from docdiff.model import Document, HeadingBlock, ListBlock, ParagraphBlock, TableBlock

from .common import make_block_id, normalize_text

_BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"}
_SKIP_ANCESTOR_TAGS = {"table", "ul", "ol"}


def _has_skipped_ancestor(tag: Tag) -> bool:
    parent = tag.parent
    while isinstance(parent, Tag):
        if parent.name in _SKIP_ANCESTOR_TAGS:
            return True
        parent = parent.parent
    return False


def _extract_table(tag: Tag, index: int) -> TableBlock:
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


def parse_html(text: str) -> Document:
    """Parse HTML text into a normalized document."""
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
        if tag.name.startswith("h"):
            level = int(tag.name[1])
            text_value = normalize_text(tag.get_text(" ", strip=True))
            if text_value:
                blocks.append(
                    HeadingBlock(
                        block_id=make_block_id("heading", block_index),
                        index=block_index,
                        level=level,
                        text=text_value,
                    )
                )
            continue

        if tag.name == "p":
            text_value = normalize_text(tag.get_text(" ", strip=True))
            if text_value:
                blocks.append(
                    ParagraphBlock(
                        block_id=make_block_id("paragraph", block_index),
                        index=block_index,
                        text=text_value,
                    )
                )
            continue

        if tag.name in {"ul", "ol"}:
            items = [
                normalize_text(item.get_text(" ", strip=True))
                for item in tag.find_all("li", recursive=False)
                if normalize_text(item.get_text(" ", strip=True))
            ]
            if items:
                blocks.append(
                    ListBlock(
                        block_id=make_block_id("list", block_index),
                        index=block_index,
                        ordered=tag.name == "ol",
                        items=items,
                    )
                )
            continue

        if tag.name == "table":
            blocks.append(_extract_table(tag, block_index))

    return Document(blocks=blocks, source_format="html")


def parse_html_file(path: Path) -> Document:
    """Parse an HTML file from disk into a normalized document."""
    return parse_html(path.read_text(encoding="utf-8"))
