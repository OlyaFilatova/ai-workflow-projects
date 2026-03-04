"""Type mapping utilities used by translators."""

from __future__ import annotations

import re

TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\\bTINYINT\\s*\\(\\s*1\\s*\\)\\b", re.IGNORECASE), "BOOLEAN"),
    (re.compile(r"\\bJSONB\\b", re.IGNORECASE), "JSON"),
    (re.compile(r"\\bSERIAL\\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\\bBIGSERIAL\\b", re.IGNORECASE), "BIGINT"),
]


def normalize_type_tokens(sql: str) -> str:
    """Apply lightweight type normalization replacements."""

    normalized = sql
    for pattern, replacement in TYPE_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized
