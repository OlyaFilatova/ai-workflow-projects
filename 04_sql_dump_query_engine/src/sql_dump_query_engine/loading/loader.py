"""Core dump-loading orchestration."""

from __future__ import annotations

import re

from ..diagnostics import WarningCollector
from ..errors import LoadError
from ..models import LoadStats, ParseEvent
from ..parsing.pg_copy import parse_copy_header, parse_copy_row
from ..parsing.splitter import split_statements
from ..translation.translator import translate_statement

_INSERT_VALUES_RE = re.compile(
    r"^(INSERT\s+INTO\s+.+?\s+VALUES\s*)(.+?)(;?)$",
    re.IGNORECASE | re.DOTALL,
)


def load_into_engine(engine: object, text: str) -> LoadStats:
    """Load dump text into DuckDB via parser/translator pipeline."""

    stats = LoadStats()
    warnings = WarningCollector()
    for event in split_statements(text):
        stats.parsed_statements += 1

        if event.kind == "copy":
            _load_copy_event(engine, event)
            stats.executed_statements += 1
            continue

        artifact = translate_statement(event)
        warnings.events.extend(artifact.warnings)

        if artifact.skipped or not artifact.sql:
            stats.skipped_statements += 1
            continue

        try:
            for statement_sql in _batch_insert_statement(artifact.sql, batch_size=500):
                getattr(engine, "execute")(statement_sql)
                stats.executed_statements += 1
        except Exception as exc:  # pragma: no cover - backend error surface
            raise LoadError(
                f"Failed to execute statement: {exc}",
                statement_line=event.statement.line,
                statement_text=event.statement.text,
            ) from exc

    stats.warnings.extend(warnings.events)
    return stats


def _load_copy_event(engine: object, event: ParseEvent) -> None:
    if event.copy_rows is None:
        return

    header = parse_copy_header(event.statement.text)
    if not event.copy_rows:
        return

    rows = [parse_copy_row(raw) for raw in event.copy_rows]
    placeholders = ", ".join("?" for _ in header.columns)
    column_sql = ", ".join(header.columns)
    insert_sql = f"INSERT INTO {header.table} ({column_sql}) VALUES ({placeholders})"

    try:
        getattr(engine, "executemany")(insert_sql, rows)
    except Exception as exc:  # pragma: no cover - backend error surface
        raise LoadError(
            f"Failed to load COPY block: {exc}",
            statement_line=event.statement.line,
            statement_text=event.statement.text,
        ) from exc


def _batch_insert_statement(sql: str, batch_size: int) -> list[str]:
    match = _INSERT_VALUES_RE.match(sql.strip())
    if not match:
        return [sql]

    prefix, values_blob, trailing_semicolon = match.groups()
    tuples = _split_tuples(values_blob)
    if len(tuples) <= batch_size:
        has_semicolon = bool(trailing_semicolon) or sql.rstrip().endswith(";")
        return [f"{prefix}{values_blob}{'' if has_semicolon else ';'}"]

    batched: list[str] = []
    for idx in range(0, len(tuples), batch_size):
        chunk = tuples[idx : idx + batch_size]
        batched.append(f"{prefix}{', '.join(chunk)};")
    return batched


def _split_tuples(values_blob: str) -> list[str]:
    tuples: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    escaped = False

    for idx, char in enumerate(values_blob):
        if char == "\\" and (in_single or in_double):
            escaped = not escaped
            continue

        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if char == "(":
                if depth == 0:
                    start = idx
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    tuples.append(values_blob[start : idx + 1].strip())
        if escaped and char != "\\":
            escaped = False

    return tuples
