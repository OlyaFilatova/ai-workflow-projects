from sql_dump_query_engine.parsing.splitter import split_statements
from sql_dump_query_engine.translation.translator import translate_statement


def test_splitter_handles_semicolon_inside_string() -> None:
    dump = "CREATE TABLE t (id INT, name TEXT);\nINSERT INTO t VALUES (1, 'a;b');\n"
    events = split_statements(dump)

    assert len(events) == 2
    assert events[1].statement.text.startswith("INSERT INTO")


def test_copy_block_emits_copy_event() -> None:
    dump = "COPY t (id) FROM stdin;\n1\n\\.\n"
    events = split_statements(dump)

    assert len(events) == 1
    assert events[0].kind == "copy"
    assert events[0].copy_rows == ["1"]


def test_unknown_type_translation_emits_lossy_warning() -> None:
    event = split_statements("CREATE TABLE t (id INT, custom FOO_TYPE);")[0]
    artifact = translate_statement(event)

    assert "TEXT" in artifact.sql
    assert any(w.code == "lossy_mapping" for w in artifact.warnings)
