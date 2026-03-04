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


class ParseError(SQLDumpError):
    """Raised when dump parsing fails."""


class TranslationError(SQLDumpError):
    """Raised when dialect translation fails."""


class LoadError(SQLDumpError):
    """Raised when translated SQL cannot be loaded."""


class QueryError(SQLDumpError):
    """Raised when query execution fails."""
