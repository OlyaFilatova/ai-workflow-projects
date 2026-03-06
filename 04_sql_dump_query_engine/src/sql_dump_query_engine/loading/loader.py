"""Core dump-loading orchestration."""

from __future__ import annotations

from ..diagnostics import WarningCollector
from ..errors import LoadError
from ..models import LoadStats, ParseEvent, TranslationArtifact
from .batching import batch_insert_statement
from ..parsing.pg_copy import parse_copy_header, parse_copy_row
from ..parsing.splitter import split_statements
from ..translation.translator import translate_statement

_INSERT_BATCH_SIZE = 500
_COPY_BATCH_SIZE = 500
_LOAD_EXECUTION_ERROR_MESSAGE = (
    "Failed to execute translated SQL during dump load. Check unsupported dialect syntax."
)
_COPY_LOAD_ERROR_MESSAGE = (
    "Failed to load PostgreSQL COPY block. Check COPY column order and value types."
)


def load_into_engine(engine: object, text: str) -> LoadStats:
    """Load dump text into DuckDB via parser/translator pipeline."""

    stats = LoadStats()
    warning_collector = WarningCollector()
    for event in split_statements(text):
        stats.parsed_statements += 1

        if event.kind == "copy":
            stats.executed_statements += _load_copy_event(engine, event)
            continue

        artifact = translate_statement(event)
        _collect_translation_warnings(warning_collector, artifact)

        if artifact.skipped or not artifact.sql:
            stats.skipped_statements += 1
            continue

        stats.executed_statements += _execute_translated_statement(engine, event, artifact.sql)

    stats.warnings.extend(warning_collector.events)
    return stats


def _collect_translation_warnings(
    warning_collector: WarningCollector,
    artifact: TranslationArtifact,
) -> None:
    warning_collector.events.extend(artifact.warnings)


def _execute_translated_statement(engine: object, event: ParseEvent, sql: str) -> int:
    executed_statement_count = 0
    try:
        for statement_sql in batch_insert_statement(sql, batch_size=_INSERT_BATCH_SIZE):
            # TODO: consider using interface for dependency inversion
            engine.execute(statement_sql)
            executed_statement_count += 1
    except Exception as exc:  # pragma: no cover - backend error surface
        raise LoadError(
            _LOAD_EXECUTION_ERROR_MESSAGE,
            statement_line=event.statement.line,
            statement_text=event.statement.text,
        ) from exc
    return executed_statement_count


def _load_copy_event(engine: object, event: ParseEvent) -> int:
    if event.copy_rows is None:
        return 0

    header = parse_copy_header(event.statement.text)
    if not event.copy_rows:
        return 0

    rows = [parse_copy_row(raw) for raw in event.copy_rows]
    placeholders = ", ".join("?" for _ in header.columns)
    column_sql = ", ".join(header.columns)
    insert_sql = f"INSERT INTO {header.table} ({column_sql}) VALUES ({placeholders})"

    executed_batch_count = 0
    try:
        for idx in range(0, len(rows), _COPY_BATCH_SIZE):
            chunk = rows[idx : idx + _COPY_BATCH_SIZE]
            engine.executemany(insert_sql, chunk)
            executed_batch_count += 1
    except Exception as exc:  # pragma: no cover - backend error surface
        raise LoadError(
            _COPY_LOAD_ERROR_MESSAGE,
            statement_line=event.statement.line,
            statement_text=event.statement.text,
        ) from exc
    return executed_batch_count
