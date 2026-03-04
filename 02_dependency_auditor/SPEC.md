# SPEC: Dependency Auditor (Source of Truth)

## 1. Product
Build a CLI application and reusable Python library that:
1. Resolves a Python project's dependency tree
2. Checks resolved packages for known vulnerabilities
3. Analyzes licenses and flags policy violations
4. Produces actionable human-readable and JSON reports

Implementation principle: library-first design with clean separation of concerns.

## 2. Supported Inputs
Supported now:
- `requirements.txt`
- `-r` includes
- PEP 508 environment markers
- Extras (e.g. `requests[socks]`)

## 3. Out of Scope
- `poetry.lock`
- `uv.lock`
- Editable installs (`-e`)
- Direct VCS/URL dependencies
- Private authenticated indexes (best-effort only)
- Full SBOM export (CycloneDX/SPDX)
- Exploitability analysis
- Private index authentication flows
- Complex dual-license legal reasoning
- Custom dependency resolver

## 4. Dependency Resolution
Resolution must:
1. Create a temporary virtual environment
2. Run `pip install -r requirements.txt`
3. Inspect installed distributions with `importlib.metadata`

## 5. Vulnerability Scanning
- Primary and only implemented vulnerability source: OSV.dev API
- Use batch API when possible
- Use simple on-disk cache with default TTL of 24h
- Architecture must allow adding additional sources later
- Supported severities:
  - LOW
  - MEDIUM
  - HIGH
  - CRITICAL

## 6. License Analysis
- Map common licenses to SPDX identifiers
- If multiple licenses are detected, treat as a simple OR expression
- Default policy: `no-gpl`
- If policy is violated, report full dependency path from root requirement
- No advanced legal compatibility engine

## 7. CLI Contract
Primary command:
- `auditpy scan -r requirements.txt [options]`

Options:
- `--json <path>`
- `--policy no-gpl`
- `--fail-on {high,critical}`
- `--verbose`

CLI output must include:
- Total packages
- Vulnerabilities grouped by severity
- License violations and warnings
- Dependency paths for findings
- Suggested remediation when possible

Exit codes:
- `0`: success, no threshold violation
- `1`: vulnerability/license threshold violated
- `2`: runtime error

## 8. JSON Output Contract
JSON output must include:
- Metadata (timestamp, Python version)
- Dependency graph (nodes and edges)
- Vulnerabilities (severity, affected package, paths)
- License findings (normalized SPDX id and policy result)

Constraint:
- JSON output schema must remain stable.

## 9. Core Models
Required core models:
- `PackageNode`
- `DependencyEdge`
- `VulnerabilityFinding`
- `LicenseFinding`
- `Report`

## 10. Documentation Requirements
- Explicitly document limitations.
- Keep scope decisions visible and consistent with this spec.
