"""Core typed models shared across package modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Dialect = Literal["mysql", "postgres", "generic"]
WarningCode = Literal["skipped_construct", "lossy_mapping", "empty_statement"]


@dataclass(slots=True)
class Statement:
    """A parsed SQL statement with source context."""

    text: str
    """Raw SQL statement text."""
    line: int
    """1-based line number where the statement begins."""
    dialect: Dialect = "generic"
    """Detected source SQL dialect."""


@dataclass(slots=True)
class ParseEvent:
    """Represents parser output for a single statement."""

    statement: Statement
    """Parsed statement metadata."""
    kind: Literal["sql", "copy", "comment"] = "sql"
    """Event type produced by the parser."""
    copy_rows: list[str] | None = None
    """COPY row payload for COPY events, otherwise ``None``."""


@dataclass(slots=True)
class WarningEvent:
    """Structured non-fatal warning data."""

    code: WarningCode
    """Stable warning code identifier."""
    message: str
    """Human-readable warning message."""
    line: int | None = None
    """Optional source line related to the warning."""


@dataclass(slots=True)
class TranslationArtifact:
    """Translator output for a single input statement."""

    original: Statement
    """Original parsed statement before translation."""
    sql: str
    """Translated SQL text."""
    skipped: bool = False
    """Whether execution should skip this statement."""
    warnings: list[WarningEvent] = field(default_factory=list)
    """Warnings generated during translation."""


@dataclass(slots=True)
class QueryResult:
    """Tabular query result."""

    columns: list[str]
    """Ordered column names."""
    rows: list[tuple[object, ...]]
    """Result rows."""


@dataclass(slots=True)
class LoadStats:
    """Dump loading counters and warning messages."""

    parsed_statements: int = 0
    """Total parse events processed."""
    executed_statements: int = 0
    """Total SQL statements executed against DuckDB."""
    skipped_statements: int = 0
    """Total statements intentionally skipped."""
    warnings: list[WarningEvent] = field(default_factory=list)
    """Collected non-fatal warnings from the load process."""
