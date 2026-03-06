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
    """Deterministic unique block identifier."""
    index: int
    """Zero-based block position in document order."""
    level: int
    """Heading depth level."""
    text: str
    """Normalized heading text."""
    block_type: Literal["heading"] = "heading"
    """Discriminator for heading block instances."""


@dataclass(slots=True)
class ParagraphBlock:
    """Normalized paragraph block."""

    block_id: str
    """Deterministic unique block identifier."""
    index: int
    """Zero-based block position in document order."""
    text: str
    """Normalized paragraph text."""
    block_type: Literal["paragraph"] = "paragraph"
    """Discriminator for paragraph block instances."""


@dataclass(slots=True)
class ListBlock:
    """Normalized list block."""

    block_id: str
    """Deterministic unique block identifier."""
    index: int
    """Zero-based block position in document order."""
    ordered: bool
    """True when list items have numeric ordering semantics."""
    items: list[str]
    """Normalized list item texts."""
    block_type: Literal["list"] = "list"
    """Discriminator for list block instances."""


@dataclass(slots=True)
class TableBlock:
    """Normalized table block."""

    block_id: str
    """Deterministic unique block identifier."""
    index: int
    """Zero-based block position in document order."""
    rows: list[list[str]]
    """Body rows represented as normalized cells."""
    header: list[str] | None = None
    """Optional header row cells."""
    block_type: Literal["table"] = "table"
    """Discriminator for table block instances."""


@dataclass(slots=True)
class ImageBlock:
    """Normalized image block metadata."""

    block_id: str
    """Deterministic unique block identifier."""
    index: int
    """Zero-based block position in document order."""
    source: str | None = None
    """Image source URI or path."""
    alt_text: str | None = None
    """Alternative text for non-visual contexts."""
    caption: str | None = None
    """Associated image caption text."""
    block_type: Literal["image"] = "image"
    """Discriminator for image block instances."""


Block = HeadingBlock | ParagraphBlock | ListBlock | TableBlock | ImageBlock


@dataclass(slots=True)
class Document:
    """Normalized document representation as an ordered list of blocks."""

    blocks: list[Block]
    """Ordered normalized blocks parsed from the input."""
    source_format: str
    """Source document format identifier."""
    metadata: dict[str, str] = field(default_factory=dict)
    """Optional parser metadata."""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)


@dataclass(slots=True)
class WordDiff:
    """Word-level token change."""

    token: str
    """Word token text."""
    change_type: ChangeType
    """Diff classification for the token."""


@dataclass(slots=True)
class DiffItem:
    """Diff entry for a pair of normalized blocks."""

    change_type: ChangeType
    """Block-level change classification."""
    before: Block | None = None
    """Block from baseline document, if present."""
    after: Block | None = None
    """Block from updated document, if present."""
    word_diffs: list[WordDiff] = field(default_factory=list)
    """Optional token-level differences for modified blocks."""


@dataclass(slots=True)
class DiffResult:
    """Complete diff output between two normalized documents."""

    granularity: Granularity
    """Requested diff granularity."""
    items: list[DiffItem]
    """Ordered diff entries across all aligned blocks."""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
