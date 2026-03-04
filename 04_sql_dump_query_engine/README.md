# SQL Dump Query Engine

Pure Python library for executing SQL queries directly against SQL dump files using DuckDB.

## Status

Project scaffolding phase. Current implementation is intentionally minimal and will expand in subsequent steps.

## Planned Scope

- Full support target: mysqldump
- Basic support target: PostgreSQL dump (including minimal COPY handling)
- Explicitly out of scope: SQLite dumps

## API (planned)

- `load_dump(path_or_text)`
- `query(sql) -> rows/columns`

## CLI (planned)

- `sqldump-query` command for loading a dump and executing SQL.

## Limitations

- Parser/translator/loader functionality is currently skeleton-only.
- Unsupported objects policy and type mapping behavior will be implemented incrementally.
