from pathlib import Path

import pytest

from sql_dump_query_engine.api import SQLDumpQueryEngine
from sql_dump_query_engine.errors import ParseError


def test_pg_copy_fixture_loads_and_queries() -> None:
    fixture = Path("tests/fixtures/pg_copy_basic.sql").read_text(encoding="utf-8")
    engine = SQLDumpQueryEngine()
    stats = engine.load_dump(fixture)

    result = engine.query("SELECT id, payload FROM events ORDER BY id")

    assert result.rows == [(1, "alpha"), (2, "beta"), (3, None)]
    assert stats.executed_statements >= 2
    assert any(warning.code == "skipped_construct" for warning in stats.warnings)


def test_pg_copy_unterminated_block_raises_parse_error() -> None:
    dump = "CREATE TABLE t (id integer);\nCOPY t (id) FROM stdin;\n1\n"
    engine = SQLDumpQueryEngine()

    with pytest.raises(ParseError):
        engine.load_dump(dump)


def test_pg_copy_escape_decoding() -> None:
    fixture = Path("tests/fixtures/pg_copy_with_escapes.sql").read_text(encoding="utf-8")
    engine = SQLDumpQueryEngine()
    engine.load_dump(fixture)

    result = engine.query("SELECT payload, note FROM logs ORDER BY id")

    assert result.rows == [("line\t1", "first\nrow"), (None, "second")]
