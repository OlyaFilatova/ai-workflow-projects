"""CLI entry point for querying SQL dumps."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from io import StringIO

from .api import SQLDumpQueryEngine
from .errors import SQLDumpError
from .models import QueryResult


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""

    parser = argparse.ArgumentParser(prog="sqldump-query")
    parser.add_argument("dump", help="Path to dump file")
    parser.add_argument("--query", required=True, help="SQL query to execute")
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint.

    Args:
        argv: Optional argv list overriding process arguments.
    """

    args = build_parser().parse_args(argv)
    engine = SQLDumpQueryEngine()
    try:
        engine.load_dump(args.dump)
        result = engine.query(args.query)
    except SQLDumpError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(_render_result(result, args.format))
    return 0


def _render_result(result: QueryResult, output_format: str) -> str:
    """Render a query result in the requested output format.

    Args:
        result: Query result object to serialize.
        output_format: One of ``table``, ``json``, or ``csv``.
    """

    if output_format == "json":
        payload = [dict(zip(result.columns, row, strict=False)) for row in result.rows]
        return json.dumps(payload, ensure_ascii=True)

    if output_format == "csv":
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(result.columns)
        writer.writerows(result.rows)
        return buffer.getvalue().rstrip("\n")

    return _render_table(result)


def _render_table(result: QueryResult) -> str:
    """Render query rows as a plain-text table.

    Args:
        result: Query result object containing column names and rows.
    """

    rows = [[str(item) for item in row] for row in result.rows]
    widths = [len(name) for name in result.columns]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    header = " | ".join(name.ljust(widths[idx]) for idx, name in enumerate(result.columns))
    divider = "-+-".join("-" * widths[idx] for idx in range(len(widths)))
    body = [" | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)) for row in rows]
    return "\n".join([header, divider, *body])
