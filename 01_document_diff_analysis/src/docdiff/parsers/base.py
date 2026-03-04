"""Parser interfaces and common types."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from docdiff.model import Document


class DocumentParser(Protocol):
    """Protocol for parser implementations that produce NDM documents."""

    def parse_text(self, text: str) -> Document:
        """Parse raw text content into a normalized document."""

    def parse_file(self, path: Path) -> Document:
        """Parse a file into a normalized document."""
