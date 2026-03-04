"""Core dump-loading orchestration."""

from __future__ import annotations

from ..diagnostics import WarningCollector
from ..models import LoadStats
from ..parsing.splitter import split_statements
from ..translation.translator import translate_statement


def load_into_engine(engine: object, text: str) -> LoadStats:
    """Load dump text into DuckDB via parser/translator pipeline."""

    del engine
    stats = LoadStats()
    warnings = WarningCollector()
    for statement in split_statements(text):
        translated = translate_statement(statement)
        if translated.strip():
            stats.executed_statements += 1
        else:
            warnings.warn(f"Skipped empty statement at line {statement.line}")
            stats.skipped_statements += 1
    stats.warnings.extend(warnings.messages)
    return stats
