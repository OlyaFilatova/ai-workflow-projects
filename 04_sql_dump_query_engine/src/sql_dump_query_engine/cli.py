"""CLI entry point for querying SQL dumps."""

from __future__ import annotations

import argparse

from .api import load_dump


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sqldump-query")
    parser.add_argument("dump", help="Path to dump file")
    parser.add_argument("sql", help="SQL query to execute")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    engine = load_dump(args.dump)
    result = engine.query(args.sql)
    print("\t".join(result.columns))
    for row in result.rows:
        print("\t".join(str(item) for item in row))
    return 0
