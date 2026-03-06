"""PostgreSQL COPY block parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import ParseError

_COPY_HEADER_RE = re.compile(
    r"^COPY\s+(?P<table>.+?)\s*\((?P<columns>.+)\)\s+FROM\s+stdin$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class CopyHeader:
    """Parsed COPY header metadata."""

    table: str
    """Target table name."""
    columns: list[str]
    """Ordered column names from the COPY header."""


def parse_copy_header(header_sql: str) -> CopyHeader:
    """Parse COPY header SQL into relation and columns.

    Args:
        header_sql: COPY header statement text.
    """

    clean = header_sql.strip().rstrip(";")
    match = _COPY_HEADER_RE.match(clean)
    if not match:
        raise ParseError(f"Unsupported COPY header: {header_sql}")
    columns = [item.strip() for item in match.group("columns").split(",")]
    table = match.group("table").strip()
    if table.lower().startswith("public."):
        table = table.split(".", maxsplit=1)[1]
    return CopyHeader(table=table, columns=columns)


def parse_copy_row(raw_row: str) -> tuple[object, ...]:
    """Parse one COPY data row.

    Args:
        raw_row: Raw tab-delimited row string from a COPY block.
    """

    values: list[object] = []
    for token in raw_row.split("\t"):
        decoded = _decode_pg_token(token)
        if decoded == r"\N":
            values.append(None)
        else:
            values.append(decoded)
    return tuple(values)


def _decode_pg_token(token: str) -> str:
    """Decode PostgreSQL COPY escape sequences.

    Args:
        token: Raw token value extracted from a COPY row.
    """

    replacements = {
        r"\\": "\\",
        r"\t": "\t",
        r"\n": "\n",
        r"\r": "\r",
    }
    decoded = token
    for key, value in replacements.items():
        decoded = decoded.replace(key, value)
    return decoded
