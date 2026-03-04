# openapi-to-sdk

`openapi-to-sdk` is a Python 3.11+ generator that converts OpenAPI 3.x specs into typed SDK code.

## Quickstart

```bash
pip install -e .[dev]
openapi-to-sdk generate --spec path/to/openapi.yaml --output ./generated_sdk
```

## Current Scope (MVP)

- OpenAPI 3.0/3.1 local files
- Local `$ref` resolution
- Parser -> IR -> template generation architecture
- Sync/async client generation and Pydantic model generation (implemented incrementally)

See `decisions.md` and `SPEC.md` for the source-of-truth scope and constraints.
