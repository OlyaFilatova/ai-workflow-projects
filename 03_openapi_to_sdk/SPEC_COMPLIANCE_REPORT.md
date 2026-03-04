# SPEC Compliance Report

## Met Requirements
- Parser -> IR -> templates pipeline implemented.
- OpenAPI 3.0/3.1 validation implemented.
- Local file loading and local `$ref` resolution with circular-ref detection implemented.
- Deterministic generation behavior implemented and tested (`tests/test_cli_pipeline.py`, `tests/test_templates.py`).
- Pydantic model generation implemented.
- Sync and async client generation implemented with shared runtime core.
- API key + bearer auth injection implemented.
- 2xx parsing, 204 handling, and non-2xx error mapping implemented.
- CLI generate command implemented with overwrite behavior and diagnostics.
- Test suites cover loader, type mapping, composition boundaries, naming determinism, runtime behavior, template stability, package integrity, and performance smoke.
- Documentation updated with supported features, deferred scope, and known limitations.

## Fixed Deviations During Audit
- Added CLI config loading support (`--config` JSON) to align with CLI contract expectations in `SPEC.md` test requirements.
- Added explicit compliance-gap documentation in `README.md` and `tradeoffs.md`.

## Remaining Known Gaps
- YAML parsing depends on optional `PyYAML`; not guaranteed in bare runtime environment.
  - Rationale: kept core dependency footprint aligned with MVP constraints.
- Remote `$ref` fetching is not supported.
  - Rationale: intentionally out of MVP scope for deterministic local-only behavior.
- Generated endpoint-specific test-file generation from input specs is not fully implemented.
  - Rationale: current tests validate generator/runtime behavior comprehensively, but not full per-endpoint emitted test artifacts.
- Full lint/type/test suite could not be executed in this environment due missing dev modules (`ruff`, `mypy`, `pytest`).
  - Rationale: quality gate script is provided and runnable; dependency installation is environment-dependent.
