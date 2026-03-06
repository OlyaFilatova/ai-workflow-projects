"""I/O helpers for parser modules."""

from __future__ import annotations

from pathlib import Path


def read_utf8_file(path: Path, file_format: str) -> str:
    """Read UTF-8 text from disk with format-aware error context."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Unable to read {file_format} file '{path}': {exc}") from exc
