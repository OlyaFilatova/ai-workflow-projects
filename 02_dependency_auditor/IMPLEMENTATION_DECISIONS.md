# Implementation Decisions Log

## 2026-03-04 - Scope baseline
Decision:
- Implement only the bounded scope from `decisions.md` and `SPEC.md`.

Why:
- Task explicitly prioritizes deliberate scope management over breadth.

Status:
- Adopted.

## 2026-03-04 - Input support
Decision:
- Support `requirements.txt` parsing with `-r` includes, markers, and extras.
- Reject editable and URL/VCS dependencies.

Why:
- Matches explicit supported/unsupported inputs in `decisions.md`.

Status:
- Implemented in `src/auditpy/parsing.py`.

## 2026-03-04 - Dependency resolution strategy
Decision:
- Resolve dependencies in a temporary virtual environment via `pip install -r`.
- Inspect installed distributions via `importlib.metadata`.

Why:
- Required by spec; avoids implementing a custom resolver.

Status:
- Implemented in `src/auditpy/resolution.py`.

## 2026-03-04 - Vulnerability provider
Decision:
- Use OSV batch API only with local cache (24h default TTL).

Why:
- Required by scope; keeps provider model simple and extensible.

Status:
- Implemented in `src/auditpy/vulnerabilities.py`.

## 2026-03-04 - License policy model
Decision:
- Normalize common license metadata to SPDX.
- Evaluate only `no-gpl` policy.
- Treat multi-license declarations as simple OR expression.

Why:
- Required bounded legal scope.

Status:
- Implemented in `src/auditpy/licenses.py`.

## 2026-03-04 - Output and exit contract
Decision:
- Provide human-readable summary + stable JSON report schema.
- Exit codes fixed to 0/1/2 per spec.

Why:
- Makes results actionable and machine-readable.

Status:
- Implemented in `src/auditpy/reporting.py` and `src/auditpy/cli.py`.

## 2026-03-04 - Testing approach
Decision:
- Favor deterministic unit/integration-style tests with mocks for network and pip/venv operations.

Why:
- Keeps CI reliable without external dependencies.

Status:
- Implemented across `tests/`.
