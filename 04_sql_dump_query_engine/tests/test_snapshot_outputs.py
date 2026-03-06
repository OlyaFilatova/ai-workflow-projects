from __future__ import annotations

import json
from pathlib import Path

from sql_dump_query_engine.loading.batching import batch_insert_statement
from sql_dump_query_engine.parsing.splitter import split_statements


def _snapshot_path(name: str) -> Path:
    return Path("tests/snapshots") / name


def _read_snapshot(name: str) -> str:
    return _snapshot_path(name).read_text(encoding="utf-8")


def test_batch_insert_statement_snapshot() -> None:
    sql = "INSERT INTO t VALUES (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'), (5, 'e');"
    batches = batch_insert_statement(sql, batch_size=2)
    rendered = json.dumps(batches, indent=2, ensure_ascii=True) + "\n"
    assert rendered == _read_snapshot("batch_insert_statement.json")


def test_split_statements_copy_snapshot() -> None:
    dump = (
        "CREATE TABLE t (id integer);\n"
        "COPY public.t (id) FROM stdin;\n"
        "1\n"
        "2\n"
        "\\.\n"
        "SELECT id FROM public.t;\n"
    )
    events = split_statements(dump)
    rendered = json.dumps(
        [
            {
                "kind": event.kind,
                "line": event.statement.line,
                "dialect": event.statement.dialect,
                "statement": event.statement.text,
                "copy_rows": event.copy_rows,
            }
            for event in events
        ],
        indent=2,
        ensure_ascii=True,
    )
    rendered = f"{rendered}\n"
    assert rendered == _read_snapshot("split_statements_copy.json")
