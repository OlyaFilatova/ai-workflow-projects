"""Shared parser utilities."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize text for deterministic comparison.

    Args:
        value: Raw text value to normalize.
    """
    nfc = unicodedata.normalize("NFC", value)
    return _WHITESPACE_RE.sub(" ", nfc).strip()


def make_block_id(prefix: str, index: int) -> str:
    """Build stable deterministic block identifiers.

    Args:
        prefix: Block type prefix.
        index: Zero-based block index.
    """
    return f"{prefix}-{index:04d}"
