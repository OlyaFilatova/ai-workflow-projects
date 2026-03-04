import json

from sql_dump_query_engine.cli import main


def test_cli_json_output(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    dump_file = tmp_path / "data.sql"
    dump_file.write_text(
        "CREATE TABLE items (id INTEGER, name TEXT);\nINSERT INTO items VALUES (1, 'a'), (2, 'b');",
        encoding="utf-8",
    )

    code = main([str(dump_file), "--query", "SELECT id, name FROM items ORDER BY id", "--format", "json"])
    captured = capsys.readouterr()

    assert code == 0
    payload = json.loads(captured.out)
    assert payload == [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]


def test_cli_failure_returns_non_zero(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    dump_file = tmp_path / "data.sql"
    dump_file.write_text("CREATE TABLE items (id INTEGER);", encoding="utf-8")

    code = main([str(dump_file), "--query", "SELECT missing FROM items"])
    captured = capsys.readouterr()

    assert code == 1
    assert "Query failed" in captured.err
    assert "statement=" in captured.err
