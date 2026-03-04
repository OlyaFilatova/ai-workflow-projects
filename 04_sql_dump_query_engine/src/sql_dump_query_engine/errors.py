"""Error hierarchy for ingestion and query execution."""

from __future__ import annotations


class SQLDumpError(Exception):
    """Base error for SQL dump query engine."""


class ParseError(SQLDumpError):
    """Raised when dump parsing fails."""


class TranslationError(SQLDumpError):
    """Raised when dialect translation fails."""


class LoadError(SQLDumpError):
    """Raised when translated SQL cannot be loaded."""


class QueryError(SQLDumpError):
    """Raised when query execution fails."""
