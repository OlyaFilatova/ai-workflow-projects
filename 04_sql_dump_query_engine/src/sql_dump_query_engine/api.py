"""Public synchronous API entrypoints."""

from __future__ import annotations

from pathlib import Path

from .engine import Engine
from .loading.loader import load_into_engine
from .models import LoadStats, QueryResult


class SQLDumpQueryEngine:
    """In-memory SQL dump query engine backed by DuckDB."""

    def __init__(self) -> None:
        self._engine = Engine()
        self._loaded = False

    def load_dump(self, path_or_text: str) -> LoadStats:
        stats = load_into_engine(self._engine, path_or_text)
        self._loaded = True
        return stats

    def query(self, sql: str) -> QueryResult:
        columns, rows = self._engine.query(sql)
        return QueryResult(columns=columns, rows=rows)


def load_dump(path_or_text: str) -> SQLDumpQueryEngine:
    """Create an engine, load dump content, and return it."""

    engine = SQLDumpQueryEngine()
    if Path(path_or_text).exists():
        text = Path(path_or_text).read_text(encoding="utf-8")
    else:
        text = path_or_text
    engine.load_dump(text)
    return engine
