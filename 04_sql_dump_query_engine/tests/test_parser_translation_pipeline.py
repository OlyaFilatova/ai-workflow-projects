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


def test_enum_translation_emits_lossy_warning() -> None:
    event = split_statements("CREATE TABLE t (id INT, state ENUM('new','done'));")[0]
    artifact = translate_statement(event)

    assert "state TEXT" in artifact.sql
    assert any(w.code == "lossy_mapping" for w in artifact.warnings)


def test_mysql_unsigned_types_are_mapped_to_duckdb_unsigned() -> None:
    event = split_statements(
        "CREATE TABLE t (a INT UNSIGNED, b BIGINT UNSIGNED, c SMALLINT UNSIGNED, d TINYINT UNSIGNED);"
    )[0]
    artifact = translate_statement(event)

    assert "a UINTEGER" in artifact.sql
    assert "b UBIGINT" in artifact.sql
    assert "c USMALLINT" in artifact.sql
    assert "d UTINYINT" in artifact.sql
    assert "UNSIGNED" not in artifact.sql.upper()


def test_mysql_table_key_clauses_are_rewritten_for_duckdb() -> None:
    event = split_statements(
        """
        CREATE TABLE `items` (
          `id` INT NOT NULL,
          `email` VARCHAR(255) NOT NULL,
          `group_id` INT,
          PRIMARY KEY (`id`),
          UNIQUE KEY `uq_items_email` (`email`),
          KEY `idx_group_id` (`group_id`)
        );
        """
    )[0]
    artifact = translate_statement(event)

    assert "UNIQUE (" in artifact.sql
    assert "UNIQUE KEY" not in artifact.sql.upper()
    assert ", KEY " not in artifact.sql.upper()


def test_create_view_is_not_skipped() -> None:
    event = split_statements("CREATE VIEW `v_users` AS SELECT `id` FROM `users`;")[0]
    artifact = translate_statement(event)

    assert artifact.skipped is False
    assert artifact.sql.startswith('CREATE VIEW "v_users" AS SELECT')


def test_detect_postgres_dialect_for_public_schema_create_table() -> None:
    event = split_statements("CREATE TABLE public.logs (id integer, payload text);")[0]
    artifact = translate_statement(event)

    assert "public." not in artifact.sql.lower()
    assert artifact.sql.startswith("CREATE TABLE logs")
