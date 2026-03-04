# auditpy

`auditpy` is a Python dependency vulnerability and license auditor.

## Current Status
This repository currently contains an initial scaffold aligned with `SPEC.md` and `decisions.md`.

## Planned Capabilities
- Resolve dependencies from `requirements.txt`
- Query OSV for vulnerabilities
- Normalize licenses and apply `no-gpl` policy
- Emit human-readable and JSON reports

## CLI (skeleton)
```bash
auditpy scan -r requirements.txt [--json report.json] [--policy no-gpl] [--fail-on high|critical] [--verbose]
```

## Scope Constraints
Out-of-scope items follow `SPEC.md` and include lockfile formats (`poetry.lock`, `uv.lock`), editable installs, VCS/URL dependencies, and advanced legal analysis.
