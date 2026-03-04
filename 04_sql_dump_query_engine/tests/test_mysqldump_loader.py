from pathlib import Path

from sql_dump_query_engine.api import SQLDumpQueryEngine


def test_mysqldump_fixture_loads_and_queries() -> None:
    fixture = Path("tests/fixtures/mysqldump_primary.sql").read_text(encoding="utf-8")
    engine = SQLDumpQueryEngine()
    stats = engine.load_dump(fixture)

    result = engine.query("SELECT id, name, active FROM users ORDER BY id")

    assert [row[0] for row in result.rows] == [1, 2, 3]
    assert result.rows[2][1] == "Eve; Mallory"
    assert stats.executed_statements >= 2
    assert any(event.code == "skipped_construct" for event in stats.warnings)


def test_unsupported_constructs_are_skipped_with_warnings() -> None:
    dump = (
        "CREATE TABLE `t` (`id` INT);\n"
        "CREATE PROCEDURE p() SELECT 1;\n"
        "INSERT INTO `t` VALUES (1);\n"
    )
    engine = SQLDumpQueryEngine()
    stats = engine.load_dump(dump)

    result = engine.query("SELECT COUNT(*) AS cnt FROM t")

    assert result.rows == [(1,)]
    assert any("unsupported" in warning.message.lower() for warning in stats.warnings)


def test_unknown_mysql_type_falls_back_to_text_with_warning() -> None:
    fixture = Path("tests/fixtures/mysqldump_unknown_type.sql").read_text(encoding="utf-8")
    engine = SQLDumpQueryEngine()
    stats = engine.load_dump(fixture)

    result = engine.query("SELECT meta FROM devices ORDER BY id")

    assert result.rows == [("point-a",), ("point-b",)]
    assert any(warning.code == "lossy_mapping" for warning in stats.warnings)
