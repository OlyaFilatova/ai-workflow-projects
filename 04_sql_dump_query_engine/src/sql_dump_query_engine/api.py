"""Public synchronous API entrypoints."""

from __future__ import annotations

from pathlib import Path

from .engine import Engine
from .errors import QueryError
from .loading.loader import load_into_engine
from .models import LoadStats, QueryResult


class SQLDumpQueryEngine:
    """In-memory SQL dump query engine backed by DuckDB."""

    def __init__(self) -> None:
        self._engine = Engine()
        self._loaded = False

    def load_dump(self, path_or_text: str) -> LoadStats:
        text = _read_path_or_text(path_or_text)
        stats = load_into_engine(self._engine, text)
        self._loaded = True
        return stats

    def query(self, sql: str) -> QueryResult:
        try:
            columns, rows = self._engine.query(sql)
        except Exception as exc:  # pragma: no cover - backend error surface
            raise QueryError(f"Query failed: {exc}", statement_text=sql) from exc
        return QueryResult(columns=columns, rows=rows)


def _read_path_or_text(path_or_text: str) -> str:
    source = Path(path_or_text)
    if source.exists():
        return source.read_text(encoding="utf-8")
    return path_or_text


def load_dump(path_or_text: str) -> SQLDumpQueryEngine:
    """Create an engine, load dump content, and return it."""

    engine = SQLDumpQueryEngine()
    engine.load_dump(path_or_text)
    return engine
