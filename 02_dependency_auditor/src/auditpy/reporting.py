"""Reporting helpers for CLI and JSON outputs."""

from __future__ import annotations

import json
from pathlib import Path

from auditpy.models import Report, Severity

SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


def render_cli_summary(report: Report) -> str:
    """Render a human-readable summary from report data."""
    severity_counts = {severity.value: 0 for severity in SEVERITY_ORDER}
    for finding in report.vulnerabilities:
        severity_counts[finding.severity.value] += 1

    license_violations = [item for item in report.licenses if item.policy_result == "violation"]
    license_warnings = [item for item in report.licenses if item.policy_result == "warn"]

    lines = [f"Total packages: {len(report.nodes)}", "Vulnerabilities by severity:"]
    for severity in SEVERITY_ORDER:
        lines.append(f"  {severity.value}: {severity_counts[severity.value]}")

    lines.append(f"License violations: {len(license_violations)}")
    lines.append(f"License warnings: {len(license_warnings)}")

    if report.vulnerabilities:
        lines.append("Vulnerability findings:")
        for finding in report.vulnerabilities:
            lines.append(f"  - {finding.package}=={finding.version} {finding.vuln_id} ({finding.severity.value})")
            for path in finding.paths:
                lines.append(f"    path: {' -> '.join(path)}")
            lines.append("    remediation: upgrade to a non-vulnerable version")

    if license_violations or license_warnings:
        lines.append("License findings:")
        for finding in [*license_violations, *license_warnings]:
            lines.append(
                f"  - {finding.package}=={finding.version} {finding.policy_result} "
                f"({finding.normalized_spdx or 'unknown'})"
            )
            for path in finding.paths:
                lines.append(f"    path: {' -> '.join(path)}")
            if finding.policy_result == "violation":
                lines.append("    remediation: replace dependency or adjust policy")

    return "\n".join(lines)


def write_json_report(report: Report, output_path: str) -> None:
    data = report.to_dict()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

