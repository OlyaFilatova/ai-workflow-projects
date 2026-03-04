"""Statement translation stubs."""

from __future__ import annotations

from ..models import ParseEvent, TranslationArtifact


def translate_statement(event: ParseEvent) -> TranslationArtifact:
    """Translate source SQL into DuckDB-compatible SQL.

    Current implementation is pass-through with minimal skip behavior.
    """

    sql = event.statement.text.strip()
    skipped = not sql
    return TranslationArtifact(original=event.statement, sql=sql, skipped=skipped)
