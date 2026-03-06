"""Shared parser utilities."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize text for deterministic comparison."""
    nfc = unicodedata.normalize("NFC", value)
    return _WHITESPACE_RE.sub(" ", nfc).strip()


def make_block_id(prefix: str, index: int) -> str:
    """Build stable deterministic block identifiers."""
    return f"{prefix}-{index:04d}"


def read_utf8_file(path: Path, file_format: str) -> str:
    """Read UTF-8 text from disk with format-aware error context."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Unable to read {file_format} file '{path}': {exc}") from exc
