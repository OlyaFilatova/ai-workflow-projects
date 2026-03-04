# Tradeoffs

## 1. Jinja2 templates over AST generation
- Decision: use Jinja2-based generation for MVP.
- Why: faster iteration and simpler extension path for prompt-driven development.
- Tradeoff: template formatting/import logic is more fragile than AST emitters for deeply complex type constructs.

## 2. Local refs only
- Decision: support local `$ref` and local relative files only.
- Why: deterministic behavior and predictable failure modes.
- Tradeoff: specs that rely on remote refs are rejected in MVP.

## 3. Focused composition subset
- Decision: support basic object-like `allOf`, simple unambiguous `oneOf`/`anyOf`; reject complex discriminator-heavy nesting.
- Why: avoid incorrect polymorphic generation while preserving useful subset.
- Tradeoff: some valid OpenAPI polymorphic specs are intentionally unsupported.

## 4. Shared sync/async runtime core
- Decision: both sync and async clients delegate to one base request-building core.
- Why: reduces divergence and test duplication.
- Tradeoff: method surface is generic; endpoint-specific ergonomics can be improved later.

## 5. Error typing strategy
- Decision: typed HTTP status exceptions for common 4xx/5xx classes plus base `ApiError`.
- Why: predictable exception handling while preserving response metadata.
- Tradeoff: per-endpoint/domain-specific error hierarchies are not generated yet.

## 6. Determinism over feature breadth
- Decision: deterministic ordering for paths/schemas/outputs and idempotent generation checks.
- Why: stable diffs and regression-friendly snapshots.
- Tradeoff: some opportunities for preserving original spec order were intentionally not prioritized.

## 7. Optional YAML parser dependency behavior
- Decision: YAML support uses `PyYAML` when available, with explicit diagnostic otherwise.
- Why: keeps core dependency set focused while allowing YAML parsing in typical dev setups.
- Tradeoff: YAML support is environment-dependent unless `PyYAML` is installed.

## 8. Quality gates as a script entrypoint
- Decision: provide `scripts/quality_gates.sh` as canonical check runner.
- Why: one command for syntax, lint, typing, and tests.
- Tradeoff: checks depend on local tool installation and cannot run in bare environments without dev deps.
