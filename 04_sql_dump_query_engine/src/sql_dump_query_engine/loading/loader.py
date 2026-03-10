"""Core dump-loading orchestration."""

from __future__ import annotations

from typing import Protocol

from ..diagnostics import WarningCollector
from ..errors import LoadError
from ..models import LoadStats, ParseEvent, TranslationArtifact
from ..parsing.pg_copy import parse_copy_header, parse_copy_row
from ..parsing.splitter import split_statements
from ..translation.translator import translate_statement
from .batching import batch_insert_statement

_INSERT_BATCH_SIZE = 500
_COPY_BATCH_SIZE = 500
_LOAD_EXECUTION_ERROR_MESSAGE = (
    "Failed to execute translated SQL during dump load. Check unsupported dialect syntax."
)
_COPY_LOAD_ERROR_MESSAGE = (
    "Failed to load PostgreSQL COPY block. Check COPY column order and value types."
)


class _LoadEngine(Protocol):
    """Minimal engine surface required by the loader."""

    def execute(self, sql: str) -> None: ...

    def executemany(self, sql: str, rows: list[tuple[object, ...]]) -> None: ...


def load_into_engine(engine: _LoadEngine, text: str) -> LoadStats:
    """Load SQL dump text into the provided engine.

    Args:
        engine: Database engine adapter with execute/executemany methods.
        text: Full SQL dump text.
    """

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
    """Collect warnings produced while translating one parse event.

    Args:
        warning_collector: Mutable warning accumulator.
        artifact: Translation result containing warning events.
    """

    warning_collector.events.extend(artifact.warnings)


def _execute_translated_statement(engine: _LoadEngine, event: ParseEvent, sql: str) -> int:
    """Execute translated SQL and return executed statement count.

    Args:
        engine: Database engine adapter with an execute method.
        event: Source parse event for contextual error reporting.
        sql: Translated SQL text to execute.
    """

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


def _load_copy_event(engine: _LoadEngine, event: ParseEvent) -> int:
    """Load rows from a PostgreSQL COPY parse event.

    Args:
        engine: Database engine adapter with an executemany method.
        event: COPY parse event with header statement and optional rows.
    """

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
