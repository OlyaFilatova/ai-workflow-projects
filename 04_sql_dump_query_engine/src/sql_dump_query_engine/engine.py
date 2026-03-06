"""DuckDB connection wrapper used by the public API."""

from __future__ import annotations

import duckdb


class Engine:
    """Simple wrapper around an in-memory DuckDB connection."""

    def __init__(self) -> None:
        """Open an in-memory DuckDB connection."""

        self.connection = duckdb.connect(database=":memory:")
        """Active DuckDB connection instance."""

    def execute(self, sql: str) -> None:
        """Execute a single SQL statement.

        Args:
            sql: SQL statement text to execute.
        """

        self.connection.execute(sql)

    def executemany(self, sql: str, rows: list[tuple[object, ...]]) -> None:
        """Execute one statement for multiple input rows.

        Args:
            sql: Parameterized SQL statement text.
            rows: Row values to bind for repeated execution.
        """

        self.connection.executemany(sql, rows)

    def query(self, sql: str) -> tuple[list[str], list[tuple[object, ...]]]:
        """Execute a query and return column names and rows.

        Args:
            sql: SQL query text to execute.
        """

        cursor = self.connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
