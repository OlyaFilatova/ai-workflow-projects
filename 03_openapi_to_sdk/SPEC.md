# SPEC: OpenAPI-to-SDK Generator (MVP)

## Purpose
Build a Python generator that converts OpenAPI 3.0/3.1 specs into an installable, typed SDK with Pydantic models and sync/async clients.

## Non-negotiable constraints
- This spec is aligned to `decisions.md` and must not expand beyond it.
- Prioritize correctness, determinism, and maintainability over feature breadth.
- Unsupported features must fail fast with clear diagnostics.

## Input support
- OpenAPI 3.0 and 3.1.
- Local spec files (JSON/YAML) with local `$ref` resolution.
- Required top-level validation and clear failure modes.

## MVP feature scope
- Operations: path/query parameters and JSON request/response bodies.
- Schemas: primitives, objects, arrays, enums, `additionalProperties`, defaults, common formats.
- Composition:
  - Supported: basic `allOf` object merges.
  - Partial: simple unambiguous `oneOf`/`anyOf` as unions.
  - Deferred: discriminator-heavy or nested advanced composition cases.
- Deferred entirely: callbacks, webhooks, multipart/form-data, complex style/explode edge cases.

## Output SDK behavior
- Python 3.11+ generated code.
- Generated package provides:
  - Pydantic v2 models.
  - Sync and async clients sharing common request-building core.
  - Operation methods derived from `operationId`; deterministic fallback naming when missing.
  - Parsed typed models for success responses.
  - Error layer: base `ApiError` plus typed status exceptions for common 4xx/5xx classes.
- Transport failures (`httpx`) stay separate from API response errors.

## Authentication and pagination
- Auth MVP: API key and bearer token.
- Pagination MVP: no generic abstraction; expose raw params and document extension path.

## Generator architecture
- Three-stage pipeline: parser -> IR -> template renderer.
- Rendering via Jinja2 templates (no AST codegen in MVP).
- Deterministic ordering/content for reproducible generation diffs.

## Packaging and dependencies
- Project and generated artifacts managed via `pyproject.toml` (PEP 621).
- Runtime dependencies: `pydantic>=2`, `httpx`, `jinja2`, `typing-extensions` when needed.
- Keep runtime dependency footprint minimal.

## Type policy
- Representative generated output must satisfy `mypy --strict`.
- Avoid `Any` except explicitly marked unsupported/opaque schema edges.

## CLI contract
- Single generate command from spec path to output package directory.
- Deterministic results across repeated runs.
- Clear diagnostics and non-zero exit on unsupported/invalid inputs.

## Test requirements
- Test framework: `pytest`.
- Required generated/behavior tests:
  - Endpoint request construction (sync + async): URL join, path interpolation/encoding, query serialization (supported subset), headers, JSON body, content-type.
  - Endpoint response parsing: typed 2xx JSON parsing, 204/empty handling, supported content-type checks.
  - Endpoint error mapping: correct exception types, preserved status/headers/body, typed error model parsing when declared.
  - Auth injection: API key/bearer application and per-call override behavior.
  - Pagination helper tests only if helpers are generated.
  - Model round-trip and alias/required-optional enforcement.
  - Enum/literal behavior including unknown-value policy.
  - Import/package smoke integrity.
- Required generator/system tests:
  - Golden snapshot codegen stability.
  - Determinism/idempotence.
  - CLI contract tests.
  - Loader tests (JSON/YAML, includes, 3.0 vs 3.1 handling).
  - `$ref` resolution tests (including recursive/circular behavior).
  - Schema mapping tests.
  - Composition subset tests + explicit unsupported-case checks.
  - Naming/collision tests.
  - Template rendering tests (`ast.parse`, imports resolve).
  - Formatting/lint compliance tests.
  - Strict typing gates.
  - Shared HTTP core tests for sync/async parity.
  - Performance/regression smoke tests for larger specs.

## Documentation requirements
- Explicitly document limitations and deferred functionality.
- Keep concerns separated in code and templates.
- Documentation must not overclaim capabilities.
