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
    line: int
    dialect: Dialect = "generic"


@dataclass(slots=True)
class ParseEvent:
    """Represents parser output for a single statement."""

    statement: Statement
    kind: Literal["sql", "copy", "comment"] = "sql"
    copy_rows: list[str] | None = None


@dataclass(slots=True)
class WarningEvent:
    """Structured non-fatal warning data."""

    code: WarningCode
    message: str
    line: int | None = None


@dataclass(slots=True)
class TranslationArtifact:
    """Translator output for a single input statement."""

    original: Statement
    sql: str
    skipped: bool = False
    warnings: list[WarningEvent] = field(default_factory=list)


@dataclass(slots=True)
class QueryResult:
    """Tabular query result."""

    columns: list[str]
    rows: list[tuple[object, ...]]


@dataclass(slots=True)
class LoadStats:
    """Dump loading counters and warning messages."""

    parsed_statements: int = 0
    executed_statements: int = 0
    skipped_statements: int = 0
    warnings: list[WarningEvent] = field(default_factory=list)
