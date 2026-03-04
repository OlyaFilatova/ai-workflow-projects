"""Error hierarchy for ingestion and query execution."""

from __future__ import annotations


class SQLDumpError(Exception):
    """Base error for SQL dump query engine with optional statement context."""

    def __init__(
        self,
        message: str,
        *,
        statement_line: int | None = None,
        statement_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.statement_line = statement_line
        self.statement_text = statement_text

    def __str__(self) -> str:
        parts = [self.message]
        if self.statement_line is not None:
            parts.append(f"line={self.statement_line}")
        if self.statement_text:
            preview = " ".join(self.statement_text.strip().split())
            parts.append(f"statement={preview[:180]}")
        return " | ".join(parts)


class ParseError(SQLDumpError):
    """Raised when dump parsing fails."""


class TranslationError(SQLDumpError):
    """Raised when dialect translation fails."""


class LoadError(SQLDumpError):
    """Raised when translated SQL cannot be loaded."""


class QueryError(SQLDumpError):
    """Raised when query execution fails."""
