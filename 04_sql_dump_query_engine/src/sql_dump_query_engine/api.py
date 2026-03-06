"""Public synchronous API entrypoints."""

from __future__ import annotations

from pathlib import Path

from .engine import Engine
from .errors import LoadError, QueryError
from .loading.loader import load_into_engine
from .models import LoadStats, QueryResult

_FILE_READ_ERROR_MESSAGE = "Failed to read dump input from file path."


class SQLDumpQueryEngine:
    """In-memory SQL dump query engine backed by DuckDB."""

    def __init__(self) -> None:
        """Initialize a fresh in-memory query engine."""

        self._engine = Engine()
        self._loaded = False

    def load_dump(self, path_or_text: str) -> LoadStats:
        """Load SQL dump content into the underlying database.

        Args:
            path_or_text: Filesystem path to a dump file or raw dump text.
        """

        text = _read_path_or_text(path_or_text)
        stats = load_into_engine(self._engine, text)
        self._loaded = True
        return stats

    def query(self, sql: str) -> QueryResult:
        """Execute a SQL query against loaded dump data.

        Args:
            sql: SQL query text to execute.
        """

        try:
            columns, rows = self._engine.query(sql)
        except Exception as exc:  # pragma: no cover - backend error surface
            raise QueryError(
                "Query failed. Verify table/column names and SQL syntax.",
                statement_text=sql,
            ) from exc
        return QueryResult(columns=columns, rows=rows)


def _read_path_or_text(path_or_text: str) -> str:
    """Resolve input as file content when possible, otherwise return raw text.

    Args:
        path_or_text: Candidate path string or SQL dump text.
    """

    source = Path(path_or_text)
    try:
        source_exists = source.exists()
    except OSError:
        # Raw SQL text can be long and invalid as a filesystem path.
        return path_or_text

    if not source_exists:
        return path_or_text

    try:
        return source.read_text(encoding="utf-8")
    except OSError as exc:
        raise LoadError(_FILE_READ_ERROR_MESSAGE, statement_text=path_or_text) from exc


def load_dump(path_or_text: str) -> SQLDumpQueryEngine:
    """Create and preload a query engine.

    Args:
        path_or_text: Filesystem path to a dump file or raw dump text.
    """

    engine = SQLDumpQueryEngine()
    engine.load_dump(path_or_text)
    return engine
