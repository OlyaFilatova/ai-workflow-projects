# openapi-to-sdk

`openapi-to-sdk` generates a typed Python SDK package from an OpenAPI 3.x file.

Current implementation status is **MVP / partial**. The tool follows `decisions.md` and `SPEC.md`, but several advanced features are intentionally deferred.

## What Is Implemented

- OpenAPI input loader:
  - OpenAPI `3.0.x` and `3.1.x` validation
  - local JSON specs
  - local YAML specs when `PyYAML` is available
  - local `$ref` resolution across files and document fragments
  - circular `$ref` detection with explicit errors
- Parser -> IR mapping:
  - operation extraction
  - deterministic naming and collision handling
  - schema mapping for primitives, arrays, enums, objects, nullable forms, and `additionalProperties`
  - basic `allOf` object merge
  - simple unambiguous `oneOf`/`anyOf` unions
- Generation:
  - deterministic package output
  - Pydantic v2 model generation
  - generated sync and async client classes with operation methods
- Runtime client behavior:
  - shared sync/async request core
  - path/query/header/json request construction
  - API key and bearer token injection with per-call override
  - response parsing for JSON and 204/empty responses
  - non-2xx error mapping to typed error classes
- CLI:
  - single `generate` command
  - supports direct args (`--spec`, `--output`)
  - deterministic output directory generation
  - `--overwrite` support

## Not Implemented / Deferred

- Remote `$ref` fetching
- Callbacks and webhooks
- `multipart/form-data` request generation
- Full OpenAPI parameter serialization matrix (`style`/`explode` edge cases)
- Advanced discriminator-heavy nested composition support
- Generic pagination abstractions
- OAuth2 flow-specific generated behavior
- Broad live end-to-end API integration tests

## Known Limitations

- YAML parsing currently depends on optional `PyYAML` availability.
- Generated response model binding is currently strongest for direct schema-model mappings; complex union/list response model hydration is limited.
- Generated tests are focused on generator/runtime behavior; full per-spec endpoint test-file generation is not implemented.
- Remote refs are explicitly rejected in MVP.
- In this environment, full quality gates (`ruff`, `mypy`, `pytest`) could not be executed because required modules were not installed.

## Installation

```bash
pip install -e .[dev]
```

## CLI Usage

Direct arguments:

```bash
openapi-to-sdk generate --spec ./openapi.json --output ./generated_sdk
```

Overwrite an existing non-empty output directory:

```bash
openapi-to-sdk generate --spec ./openapi.json --output ./generated_sdk --overwrite
```

## Development Quality Gates

```bash
./scripts/quality_gates.sh
```

This runs syntax compilation, `ruff`, `mypy`, and `pytest`.

## Project Structure

- `src/openapi_to_sdk/parser`: OpenAPI loading and `$ref` resolution
- `src/openapi_to_sdk/ir`: IR models and OpenAPI -> IR mapping
- `src/openapi_to_sdk/generator`: template rendering and generation pipeline
- `src/openapi_to_sdk/runtime`: shared sync/async HTTP runtime and errors
- `src/openapi_to_sdk/templates`: Jinja2 templates for generated package files
- `tests`: unit, template, runtime, and CLI tests
