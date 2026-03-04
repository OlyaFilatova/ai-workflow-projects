"""Core dump-loading orchestration."""

from __future__ import annotations

from ..diagnostics import WarningCollector
from ..errors import LoadError
from ..models import LoadStats
from ..parsing.splitter import split_statements
from ..translation.translator import translate_statement


def load_into_engine(engine: object, text: str) -> LoadStats:
    """Load dump text into DuckDB via parser/translator pipeline."""

    stats = LoadStats()
    warnings = WarningCollector()
    for event in split_statements(text):
        stats.parsed_statements += 1
        artifact = translate_statement(event)
        if artifact.skipped or not artifact.sql:
            warnings.warn("empty_statement", "Skipped empty statement", event.statement.line)
            stats.skipped_statements += 1
            continue

        try:
            getattr(engine, "execute")(artifact.sql)
            stats.executed_statements += 1
            warnings.events.extend(artifact.warnings)
        except Exception as exc:  # pragma: no cover - backend error surface
            raise LoadError(
                f"Failed to execute statement: {exc}",
                statement_line=event.statement.line,
                statement_text=event.statement.text,
            ) from exc

    stats.warnings.extend(warnings.events)
    return stats
