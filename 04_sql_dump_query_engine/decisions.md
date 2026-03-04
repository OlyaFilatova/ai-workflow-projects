- Format support boundary
    * Full support: mysqldump.
    * Basic support: PostgreSQL dumps (including COPY blocks at minimal viable level).
    * Out of scope: SQLite dump.

- Query engine contract
    * Execute user queries with DuckDB SQL semantics.

- Parser/loader architecture
    * Statement parser + dedicated COPY block parser.
    * Translate DDL/DML into DuckDB-compatible SQL before execution.
    * Stream large inserts/copy data in batches.

- Type mapping baseline
    * Explicit mappings for booleans, unsigned integer variants, serial/sequence equivalents, temporal types, enum/json.
    * Unknown types fall back to TEXT with warnings.

- Unsupported objects policy
    * Support basic CREATE VIEW ingestion.
    * Skip triggers/procedures/functions with clear warnings.
    * Support core table/schema/data path first.

- API shape
    * Simple synchronous Python API:
      * load_dump(path_or_text)
      * query(sql) -> rows/columns
    * Keep adapters (pandas/polars) optional and out of core.

- Error/warning behavior
    * Raise structured exceptions with statement context.
    * Emit warnings for lossy translations and skipped constructs.

- Test minimum for confidence
    * Realistic mysqldump fixtures + basic pg_dump fixture.
    * Query-result assertions for correctness.
    * Negative tests for unsupported syntax paths.

- Documentation minimum
    * README with quick start, supported features, and explicit limitations.
    * Compatibility notes for known unsupported dump features.
