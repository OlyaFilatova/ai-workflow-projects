from pathlib import Path

import pytest

from sql_dump_query_engine.api import SQLDumpQueryEngine, load_dump
from sql_dump_query_engine.errors import LoadError, QueryError
from sql_dump_query_engine.models import LoadStats


def test_load_dump_from_text_and_query() -> None:
    dump = "CREATE TABLE t (id INTEGER);\nINSERT INTO t VALUES (1), (2);"
    engine = load_dump(dump)
    result = engine.query("SELECT id FROM t ORDER BY id")

    assert result.columns == ["id"]
    assert result.rows == [(1,), (2,)]


def test_load_dump_from_long_text_is_not_treated_as_path() -> None:
    large_comment = "x" * 320
    dump = f"-- {large_comment}\nCREATE TABLE t_long (id INTEGER);\nINSERT INTO t_long VALUES (1);"
    engine = load_dump(dump)
    result = engine.query("SELECT id FROM t_long")

    assert result.rows == [(1,)]


def test_load_dump_from_path(tmp_path: Path) -> None:
    dump_file = tmp_path / "sample.sql"
    dump_file.write_text("CREATE TABLE items (id INTEGER);\nINSERT INTO items VALUES (7);", encoding="utf-8")

    engine = SQLDumpQueryEngine()
    stats = engine.load_dump(str(dump_file))
    result = engine.query("SELECT id FROM items")

    assert isinstance(stats, LoadStats)
    assert stats.executed_statements == 2
    assert result.rows == [(7,)]


def test_query_error_contains_statement_context() -> None:
    engine = SQLDumpQueryEngine()
    with pytest.raises(QueryError) as exc:
        engine.query("SELECT * FROM missing_table")

    assert exc.value.statement_text == "SELECT * FROM missing_table"


def test_load_error_contains_statement_context() -> None:
    engine = SQLDumpQueryEngine()
    with pytest.raises(LoadError) as exc:
        engine.load_dump("CREATE TABLE bad (id INTEGER)\nINSERT INTO bad VALUES (1);")

    assert exc.value.statement_line == 1
    assert "CREATE TABLE bad" in (exc.value.statement_text or "")


def test_load_dump_from_unreadable_existing_path_raises_load_error(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = SQLDumpQueryEngine()

    monkeypatch.setattr(Path, "exists", lambda self: True)

    def _raise_os_error(self: Path, encoding: str = "utf-8") -> str:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", _raise_os_error)

    with pytest.raises(LoadError) as exc:
        engine.load_dump("/tmp/unreadable.sql")

    assert "Failed to read dump input from file path." in str(exc.value)
    assert exc.value.statement_text == "/tmp/unreadable.sql"
