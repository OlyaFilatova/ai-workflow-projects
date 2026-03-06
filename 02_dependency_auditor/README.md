# auditpy

`auditpy` audits Python dependencies for vulnerabilities and license policy issues.
It is implemented as a reusable library with a CLI frontend.

## What Works
- Parses `requirements.txt` with support for:
  - recursive `-r` includes
  - PEP 508 environment markers
  - extras (for example `requests[socks]`)
- Resolves dependencies by:
  - creating a temporary virtual environment
  - running `pip install -r requirements.txt`
  - inspecting installed distributions via `importlib.metadata`
- Queries OSV.dev batch API for vulnerabilities with on-disk cache (default TTL 24h)
- Normalizes common licenses to SPDX and evaluates policy (default `no-gpl`)
- Produces:
  - human-readable CLI summary
  - stable JSON report (`metadata`, `dependency_graph`, `vulnerabilities`, `license_findings`)
- Exit codes:
  - `0` success, no threshold violation
  - `1` vulnerability/license threshold violated
  - `2` runtime error

## Supported Inputs
- `requirements.txt`
- `-r` included requirement files
- PEP 508 markers
- extras

## CLI Usage
```bash
auditpy scan -r requirements.txt
auditpy scan -r requirements.txt --json report.json
auditpy scan -r requirements.txt --policy no-gpl --fail-on critical --verbose
```

## Example CLI Output
```text
Total packages: 12
Vulnerabilities by severity:
  LOW: 0
  MEDIUM: 1
  HIGH: 1
  CRITICAL: 0
License violations: 1
License warnings: 0
Vulnerability findings:
  - urllib3==2.2.0 OSV-2024-XXXX (HIGH)
    path: requests -> urllib3
    remediation: upgrade to a non-vulnerable version
License findings:
  - somepkg==1.4.2 violation (GPL-3.0-only)
    path: myapp -> somepkg
    remediation: replace dependency or adjust policy
```

## Example JSON Report Shape
```json
{
  "metadata": {"timestamp": "...", "python_version": "3.13.2"},
  "dependency_graph": {"nodes": [], "edges": []},
  "vulnerabilities": [],
  "license_findings": []
}
```

## Limitations and Out of Scope
Aligned with `SPEC.md` / `decisions.md`:
- Not supported:
  - `poetry.lock`
  - `uv.lock`
  - editable installs (`-e`)
  - direct VCS/URL dependencies
  - private index authentication flows
  - full SBOM export (CycloneDX/SPDX)
  - exploitability analysis
  - advanced legal compatibility engine
  - custom dependency resolver
- Vulnerability source is OSV only (architecture allows future extension).
- License normalization covers common identifiers and may emit warnings for unknown metadata.

## Tradeoffs and Current Gaps
- Resolution is network-dependent because it relies on `pip install`.
- Live OSV behavior is mocked in tests; CI does not require network access.
- Policy support is intentionally minimal (`no-gpl` only) to preserve bounded scope.

## Developer Notes
Run tests:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
```

Run local scan:
```bash
PYTHONPATH=src python3 -m auditpy scan -r requirements.txt --json report.json
```

Install editable package in your own virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```
