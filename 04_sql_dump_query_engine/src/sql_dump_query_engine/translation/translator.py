"""Statement translation stubs."""

from __future__ import annotations

from ..models import Statement


def translate_statement(statement: Statement) -> str:
    """Translate source SQL into DuckDB-compatible SQL.

    Scaffold: currently pass-through.
    """

    return statement.text
