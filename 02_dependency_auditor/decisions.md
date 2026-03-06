- The tool is a CLI application and reusable Python library that:
    1. Resolves a Python project's dependency tree
    2. Checks resolved packages for known vulnerabilities
    3. Analyzes licenses and flags policy violations
    4. Produces actionable human-readable and JSON reports
- Library-first design
- Supported inputs
    * `requirements.txt`
        * Supports `-r` includes
        * Supports PEP 508 environment markers
        * Supports extras (e.g. `requests[socks]`)
- Out of scope
    * `poetry.lock`
    * `uv.lock`
    * Editable installs (`-e`)
    * Direct VCS/URL dependencies
    * Private authenticated indexes (best-effort only)
    * Full SBOM (CycloneDX/SPDX) export
    * Exploitability analysis
    * Private index authentication flows
    * Complex dual-license legal reasoning
    * Custom dependency resolver
- Dependency Resolution MUST:
    1. Create a temporary virtual environment
    2. Use `pip install -r requirements.txt`
    3. Inspect installed distributions using `importlib.metadata`
- Vulnerability data source
    * Primary vulnerability source: OSV.dev API
    * No other data sources should be implemented but architecture must allow easily adding other sources.
    * Use batch API when possible
    * Implement simple on-disk cache with TTL (default 24h)
- Supported severities:
    * LOW
    * MEDIUM
    * HIGH
    * CRITICAL
- Map common licenses to SPDX identifiers
- If multiple licenses are detected, treat as a simple OR expression.
- Default policy: `no-gpl`
- If a policy violation occurs Report full dependency path from root requirement
- No advanced legal compatibility engine will be implemented.

- CLI Output
    * Total packages
    * Vulnerabilities grouped by severity
    * License violations and warnings
    * Dependency paths for findings
    * Suggested remediation when possible

- JSON Output
    * Metadata (timestamp, python version)
    * Dependency graph (nodes and edges)
    * Vulnerabilities (with severity, affected package, paths)
    * License findings (with normalized SPDX id and policy result)
- JSON Output Schema must remain stable.

- CLI Specification
    * Primary command:
        ```
        auditpy scan -r requirements.txt [options]
        ```
        - Options:
            * `--json <path>`
            * `--policy no-gpl`
            * `--fail-on {high,critical}`
            * `--verbose`

    * Exit codes:
        * 0 → success, no threshold violation
        * 1 → vulnerability/license threshold violated
        * 2 → runtime error

- Core models:
    * PackageNode
    * DependencyEdge
    * VulnerabilityFinding
    * LicenseFinding
    * Report

- Explicitly documented limitations
- Clean separation of concerns