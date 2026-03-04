"""Core typed models shared across package modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Statement:
    """A parsed SQL statement with source context."""

    text: str
    line: int


@dataclass(slots=True)
class QueryResult:
    """Tabular query result."""

    columns: list[str]
    rows: list[tuple[object, ...]]


@dataclass(slots=True)
class LoadStats:
    """Dump loading counters and warning messages."""

    executed_statements: int = 0
    skipped_statements: int = 0
    warnings: list[str] = field(default_factory=list)
