"""Type mapping placeholders used by translators."""

from __future__ import annotations


TYPE_MAP: dict[str, str] = {
    "tinyint(1)": "BOOLEAN",
    "jsonb": "JSON",
}


def map_type(source_type: str) -> str:
    return TYPE_MAP.get(source_type.lower(), source_type)
