# SQL Dump Query Engine

Pure Python library for executing SQL queries directly against SQL dump files using DuckDB.

## Quick Start

```bash
pip install -e .
sqldump-query dump.sql --query "SELECT COUNT(*) FROM users"
```

Python API:

```python
from sql_dump_query_engine import load_dump

engine = load_dump("dump.sql")
result = engine.query("SELECT id, name FROM users ORDER BY id")
print(result.columns)
print(result.rows)
```

## Status

Working baseline implementation with:
- Primary support: mysqldump (table/data path)
- Basic support: PostgreSQL dumps including minimal `COPY ... FROM stdin` ingestion
- Explicitly out of scope: SQLite dumps

## Library API

- `load_dump(path_or_text)`
- `query(sql) -> rows/columns`

## CLI

Command:
- `sqldump-query <dump-path> --query "<sql>" [--format table|json|csv]`

Examples:
- `sqldump-query dump.sql --query "SELECT COUNT(*) FROM users"`
- `sqldump-query dump.sql --query "SELECT id,name FROM users" --format json`

CLI behavior:
- Non-zero exit code on load/query failures.
- Error output includes contextual statement details when available.

## Usage and Security Notes

- Treat dump files as executable SQL input. Load only trusted dumps.
- Treat `query(sql)` and `--query` as raw SQL execution. Do not pass untrusted user input directly.
- If you build queries from user input, use parameterized SQL in your own wrapper layer and strict allowlists for identifiers (table/column names).
- For shared or multi-tenant environments, consider allowing only read-only `SELECT` queries and blocking mutating statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.).
- This tool is designed for local analysis workflows, not as a hardened SQL sandbox for untrusted users.

## Supported Features

- mysqldump:
  - `CREATE TABLE`
  - `INSERT INTO ... VALUES ...` (including multi-row batching)
  - handling of common dump directives/comments
- PostgreSQL:
  - basic table/data ingestion
  - dedicated parsing for `COPY ... FROM stdin` blocks with batch loading

## Unsupported / Limited

- Views, triggers, procedures, functions are skipped with warnings.
- PostgreSQL support is intentionally basic and not full dialect coverage.
- Unsupported/unknown column types fallback to `TEXT` with lossy-mapping warnings.
- Advanced dump constructs may fail with contextual errors.
