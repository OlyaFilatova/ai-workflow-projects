- Scope
    * OpenAPI 3.0/3.1 input.
    * Local file specs with local `$ref` resolution.
    * Support JSON request/response bodies and path/query parameters.
    * Defer callbacks, webhooks, multipart/form-data, and complex style/explode edge cases.

- Composition
    * Support basic `allOf` object merges.
    * Support simple, unambiguous `oneOf`/`anyOf` as `Union`.
    * Defer discriminator-heavy and nested advanced compositions.

- Runtime and packaging
    * Target Python 3.11+.
    * Runtime deps: `pydantic>=2`, `httpx`, `jinja2`, `typing-extensions` when needed.
    * Keep runtime deps minimal.
    * Use `pyproject.toml` (PEP 621).

- Generator architecture
    * 3-stage pipeline: parser -> IR -> templates.
    * Use Jinja2 templates in MVP (no AST codegen).

- Generated client surface
    * Generate sync and async clients with a shared request builder/core.
    * Method names from `operationId`; deterministic fallback when missing.
    * Successful responses return parsed Pydantic models.

- Errors
    * Generate base `ApiError` plus typed status exceptions for common 4xx/5xx classes.
    * Keep transport errors (`httpx`) distinct from API response errors.

- Type safety
    * Enforce `mypy --strict` for representative generated fixtures.
    * Avoid `Any` except explicitly marked unsupported/opaque schema edges.

- Auth and pagination
    * Auth MVP: API key and bearer token.
    * No generic pagination abstraction in MVP; expose raw params and document extension path.

- CLI and generation behavior
    * Single command to generate SDK from spec to output package directory.
    * Deterministic file ordering/content for reproducible diffs.
    * Fail fast on unsupported features with clear diagnostics.

- Tests generated from OpenAPI
    * Per-endpoint request construction tests (sync): URL join, path interpolation/encoding, query serialization (supported styles), headers, JSON body, content-type.
    * Per-endpoint request construction tests (async): same assertions for async client.
    * Per-endpoint response parsing tests: 2xx JSON to typed model/list, 204/empty body, expected content-type handling (supported subset).
    * Per-endpoint error mapping tests: representative non-2xx raises correct exception, preserving status/headers/body; parse typed error models when declared.
    * Authentication injection tests: API key/bearer injection, per-call override vs client defaults.
    * Pagination helper tests (only if helpers are generated): iterator/async iterator behavior and stop conditions.
    * Model round-trip tests: `model_validate`/`model_dump`, alias behavior for invalid identifiers, required/optional enforcement.
    * Enum/literal tests: validation/serialization and unknown-value policy behavior.
    * Package integrity smoke test: generated package imports cleanly, no missing modules, exports consistency (if generated).
    * Out of scope: broad live end-to-end API tests.

- Overall testing strategy
    * Use `pytest`.
    * Golden snapshot tests: fixed specs produce stable generated output (normalized).
    * Determinism/idempotence tests: two generations are identical (post-format), with stable ordering.
    * CLI contract tests: flags, config loading, overwrite behavior, exit codes, readable diagnostics.
    * OpenAPI loader tests: JSON/YAML parsing, relative includes, 3.0 vs 3.1 handling, required top-level validation.
    * `$ref` resolution tests: local/remote refs, caching, recursive/circular refs, clear failure modes.
    * Schema-to-type mapping tests: required/optional, nullability (3.0 nullable vs 3.1 null union), arrays, `additionalProperties`, enums, defaults, formats (date/datetime/uuid).
    * Composition subset tests: `allOf` flattening, simple `oneOf`, explicit unsupported errors for out-of-scope discriminator/nested cases.
    * Naming/collision tests: snake_case/PascalCase, reserved keywords, duplicates, stable disambiguation.
    * Template rendering tests: template fixtures render, generated code parses (`ast.parse`), imports resolve.
    * Formatting/lint integration: generated code is black/ruff compliant and imports are stable.
    * Strict typing gates: `mypy --strict` over generator code (if typed) and representative generated SDKs.
    * HTTP client core tests: shared request/response helpers behave correctly in sync/async.
    * Performance/regression smoke: large spec generation avoids pathological time/memory and ref-resolution blowups.

- Quality bar
    * Explicitly document limitations.
    * Keep separation of concerns clean.
    * Documentation must not overclaim capabilities.
