"""Type mapping utilities used by translators."""

from __future__ import annotations

import re

from ._sql_defs import split_definitions

TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bTINYINT\s*\(\s*1\s*\)\s+UNSIGNED\b", re.IGNORECASE), "BOOLEAN"),
    (re.compile(r"\bBIGINT\s+UNSIGNED\b", re.IGNORECASE), "UBIGINT"),
    (re.compile(r"\b(?:INT|INTEGER|MEDIUMINT)\s+UNSIGNED\b", re.IGNORECASE), "UINTEGER"),
    (re.compile(r"\bSMALLINT\s+UNSIGNED\b", re.IGNORECASE), "USMALLINT"),
    (re.compile(r"\bTINYINT\s+UNSIGNED\b", re.IGNORECASE), "UTINYINT"),
    (re.compile(r"\bMEDIUMINT\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bTINYINT\s*\(\s*1\s*\)\b", re.IGNORECASE), "BOOLEAN"),
    (re.compile(r"\bJSONB\b", re.IGNORECASE), "JSON"),
    (re.compile(r"\bSERIAL\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bBIGSERIAL\b", re.IGNORECASE), "BIGINT"),
    (re.compile(r"\bDATETIME\b", re.IGNORECASE), "TIMESTAMP"),
    (
        re.compile(r"\bTIMESTAMP\s+WITHOUT\s+TIME\s+ZONE\b", re.IGNORECASE),
        "TIMESTAMP",
    ),
    (
        re.compile(r"\bTIMESTAMP\s+WITH\s+TIME\s+ZONE\b", re.IGNORECASE),
        "TIMESTAMPTZ",
    ),
    (re.compile(r"\bUNSIGNED\b", re.IGNORECASE), ""),
]

_KNOWN_TYPES = {
    "BIGINT",
    "BLOB",
    "BOOLEAN",
    "CHAR",
    "DATE",
    "DATETIME",
    "DECIMAL",
    "DOUBLE",
    "FLOAT",
    "INT",
    "INTEGER",
    "JSON",
    "NUMERIC",
    "REAL",
    "SMALLINT",
    "TEXT",
    "TIME",
    "TIMESTAMP",
    "TIMESTAMPTZ",
    "UBIGINT",
    "UINTEGER",
    "USMALLINT",
    "UTINYINT",
    "VARCHAR",
}


def normalize_type_tokens(sql: str) -> str:
    """Apply lightweight type normalization replacements."""

    normalized = sql
    for pattern, replacement in TYPE_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def apply_enum_fallback(sql: str) -> tuple[str, list[str]]:
    """Map ENUM definitions to TEXT and emit lossy warnings."""

    warnings: list[str] = []

    def replace_enum(match: re.Match[str]) -> str:
        warnings.append("ENUM mapped to TEXT")
        return "TEXT"

    translated = re.sub(r"\bENUM\s*\([^)]*\)", replace_enum, sql, flags=re.IGNORECASE)
    return translated, warnings


def apply_unknown_type_fallback(sql: str) -> tuple[str, list[str]]:
    """Replace unsupported CREATE TABLE column types with TEXT."""

    stripped_upper = sql.strip().upper()
    if not stripped_upper.startswith("CREATE TABLE"):
        return sql, []

    open_idx = sql.find("(")
    close_idx = sql.rfind(")")
    if open_idx == -1 or close_idx == -1 or close_idx <= open_idx:
        return sql, []

    body = sql[open_idx + 1 : close_idx]
    definitions = split_definitions(body)
    warnings: list[str] = []
    rewritten: list[str] = []

    for definition in definitions:
        candidate = definition.strip()
        if not candidate:
            rewritten.append(definition)
            continue

        first_token = candidate.split(maxsplit=1)[0].upper().strip('"`')
        if first_token in {"PRIMARY", "UNIQUE", "KEY", "CONSTRAINT", "FOREIGN", "CHECK"}:
            rewritten.append(definition)
            continue

        match = re.match(
            r'(?P<indent>\s*)(?P<name>"[^"]+"|`[^`]+`|[A-Za-z_][\w$]*)\s+(?P<type>[A-Za-z][A-Za-z0-9_]*(?:\s*\([^)]*\))?)',
            definition,
        )
        if not match:
            rewritten.append(definition)
            continue

        type_token = match.group("type")
        base_type = type_token.split("(", maxsplit=1)[0].strip().upper()
        if base_type in _KNOWN_TYPES:
            rewritten.append(definition)
            continue

        span_start, span_end = match.span("type")
        replaced = f"{definition[:span_start]}TEXT{definition[span_end:]}"
        rewritten.append(replaced)
        warnings.append(f"Unknown type '{type_token}' mapped to TEXT")

    new_body = ",\n".join(segment.strip("\n") for segment in rewritten)
    translated = f"{sql[:open_idx + 1]}\n{new_body}\n{sql[close_idx:]}"
    return translated, warnings
