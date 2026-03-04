"""Dataclass models for normalized documents and diff results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ChangeType = Literal["added", "removed", "modified", "equal"]
Granularity = Literal["block", "block+word", "word"]


@dataclass(slots=True)
class HeadingBlock:
    """Normalized heading block."""

    block_id: str
    index: int
    level: int
    text: str
    block_type: Literal["heading"] = "heading"


@dataclass(slots=True)
class ParagraphBlock:
    """Normalized paragraph block."""

    block_id: str
    index: int
    text: str
    block_type: Literal["paragraph"] = "paragraph"


@dataclass(slots=True)
class ListBlock:
    """Normalized list block."""

    block_id: str
    index: int
    ordered: bool
    items: list[str]
    block_type: Literal["list"] = "list"


@dataclass(slots=True)
class TableBlock:
    """Normalized table block."""

    block_id: str
    index: int
    rows: list[list[str]]
    header: list[str] | None = None
    block_type: Literal["table"] = "table"


@dataclass(slots=True)
class ImageBlock:
    """Normalized image block metadata."""

    block_id: str
    index: int
    source: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    block_type: Literal["image"] = "image"


Block = HeadingBlock | ParagraphBlock | ListBlock | TableBlock | ImageBlock


@dataclass(slots=True)
class Document:
    """Normalized document representation as an ordered list of blocks."""

    blocks: list[Block]
    source_format: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)


@dataclass(slots=True)
class WordDiff:
    """Word-level token change."""

    token: str
    change_type: ChangeType


@dataclass(slots=True)
class DiffItem:
    """Diff entry for a pair of normalized blocks."""

    change_type: ChangeType
    before: Block | None = None
    after: Block | None = None
    word_diffs: list[WordDiff] = field(default_factory=list)


@dataclass(slots=True)
class DiffResult:
    """Complete diff output between two normalized documents."""

    granularity: Granularity
    items: list[DiffItem]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
