"""DuckDB connection wrapper used by the public API."""

from __future__ import annotations

import duckdb


class Engine:
    """Simple wrapper around an in-memory DuckDB connection."""

    def __init__(self) -> None:
        self.connection = duckdb.connect(database=":memory:")

    def execute(self, sql: str) -> None:
        self.connection.execute(sql)

    def executemany(self, sql: str, rows: list[tuple[object, ...]]) -> None:
        self.connection.executemany(sql, rows)

    def query(self, sql: str) -> tuple[list[str], list[tuple[object, ...]]]:
        cursor = self.connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
