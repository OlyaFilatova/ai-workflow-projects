# SPEC Compliance Summary

Audit date: 2026-03-04
Source of truth: `SPEC.md`

## Requirement Mapping
| Requirement | Implementation location | Test coverage | Remaining gap |
|---|---|---|---|
| CLI + library architecture | `src/auditpy/cli.py`, `src/auditpy/*` | `tests/test_cli_reporting.py` | None |
| Supported input: `requirements.txt`, `-r`, markers, extras | `src/auditpy/parsing.py` | `tests/test_parsing.py` | None |
| Reject `-e` and URL/VCS deps | `src/auditpy/parsing.py` | `tests/test_parsing.py` | None |
| Resolution via temp venv + `pip install -r` + metadata inspection | `src/auditpy/resolution.py` | `tests/test_resolution.py` | None |
| OSV-only vulnerability source, batch API, cache TTL 24h | `src/auditpy/vulnerabilities.py` | `tests/test_vulnerabilities.py` | None |
| Severity support LOW/MEDIUM/HIGH/CRITICAL | `src/auditpy/models.py`, `src/auditpy/vulnerabilities.py` | `tests/test_models.py`, `tests/test_vulnerabilities.py` | None |
| SPDX normalization + `no-gpl` policy + OR license expression | `src/auditpy/licenses.py` | `tests/test_licenses.py` | None |
| Full dependency paths in findings | `src/auditpy/resolution.py`, `src/auditpy/vulnerabilities.py`, `src/auditpy/licenses.py` | `tests/test_resolution.py`, `tests/test_licenses.py`, `tests/test_vulnerabilities.py` | None |
| CLI output: totals, severity groups, license findings, paths, remediation | `src/auditpy/reporting.py`, `src/auditpy/cli.py` | `tests/test_reporting.py`, `tests/test_cli_reporting.py` | None |
| JSON output with stable schema | `src/auditpy/models.py`, `src/auditpy/reporting.py` | `tests/test_models.py`, `tests/test_cli_reporting.py` | None |
| Exit codes 0/1/2 | `src/auditpy/cli.py` | `tests/test_cli_reporting.py` | None |
| Core models (`PackageNode`, `DependencyEdge`, `VulnerabilityFinding`, `LicenseFinding`, `Report`) | `src/auditpy/models.py` | `tests/test_models.py` | None |
| Explicitly documented limitations | `README.md`, `IMPLEMENTATION_DECISIONS.md` | documentation review | None |

## Scope-Creep Check
- No additional input format support beyond `requirements.txt` family.
- No additional vulnerability providers beyond OSV.
- No advanced legal compatibility engine.
- No SBOM exporter implemented.

## Known Operational Constraints
- Live scans require network access for dependency installation and OSV queries.
- Test suite uses mocks for network and pip operations to remain deterministic in CI.
