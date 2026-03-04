# SPEC

## Purpose
Build a Python library that executes SQL queries directly against SQL dump files using DuckDB, without running source database servers.

## Scope
- Full support target: `mysqldump`.
- Basic support target: PostgreSQL dumps, including minimal viable `COPY ... FROM stdin` handling.
- Explicitly out of scope: SQLite dump support.

## Execution Backend
- Use DuckDB as the SQL execution engine.

## Ingestion Architecture
- Parse dump input with:
  - A general SQL statement parser/splitter.
  - A dedicated parser for PostgreSQL `COPY ... FROM stdin` data blocks.
- Translate DDL/DML into DuckDB-compatible SQL before execution.
- Load large multi-row payloads (`INSERT`/`COPY`) in batches.

## Type Mapping
- Provide explicit mapping rules for:
  - booleans
  - serial/sequence equivalents
  - temporal types
  - enum
  - JSON/JSONB
- For unknown/unhandled source types, fallback to `TEXT` and emit a warning.

## Unsupported Objects Policy
- Skip views, triggers, procedures, and functions.
- Emit clear warnings when these constructs are encountered.
- Prioritize table/schema/data ingestion path.

## Public API
- Core synchronous API:
  - `load_dump(path_or_text)`
  - `query(sql) -> rows/columns`
- Dataframe adapters (e.g., pandas/polars) are optional and not part of core.

## Errors and Warnings
- Raise structured exceptions with statement context.
- Emit warnings for:
  - lossy translations
  - skipped unsupported constructs

## Quality Minimum
- Tests must include:
  - realistic mysqldump fixtures
  - at least one pg_dump fixture
  - query-result correctness assertions
  - negative tests for unsupported syntax paths
- Documentation must include:
  - quick start
  - supported features
  - explicit limitations
