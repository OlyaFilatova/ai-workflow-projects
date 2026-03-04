"""PostgreSQL COPY parsing placeholders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CopyBlock:
    header: str
    rows: list[str]


def extract_copy_blocks(_: str) -> list[CopyBlock]:
    """Extract PostgreSQL COPY blocks.

    Placeholder implementation to be expanded in later prompts.
    """

    return []
