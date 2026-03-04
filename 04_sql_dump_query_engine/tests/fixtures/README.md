# Fixture Catalog

- `mysqldump_primary.sql`: baseline mysqldump fixture covering DDL, multi-row inserts, directives, and unsupported object skipping.
- `pg_copy_basic.sql`: baseline pg_dump fixture covering table DDL, COPY block ingestion, and unsupported object skipping.
- `mysqldump_unknown_type.sql`: mysqldump fixture with unsupported column type to validate TEXT fallback + warning behavior.
- `pg_copy_with_escapes.sql`: PostgreSQL COPY fixture with escaped tokens and null handling.
