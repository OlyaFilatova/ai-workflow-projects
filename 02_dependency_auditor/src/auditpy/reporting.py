"""Reporting helpers for CLI and JSON outputs."""

from __future__ import annotations

import json
from pathlib import Path

from auditpy.models import LicenseFinding, Report, Severity

SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
SUMMARY_TOTAL_PACKAGES_LABEL = "Total packages"
SUMMARY_VULNERABILITIES_LABEL = "Vulnerabilities by severity:"
SUMMARY_LICENSE_VIOLATIONS_LABEL = "License violations"
SUMMARY_LICENSE_WARNINGS_LABEL = "License warnings"
SUMMARY_VULNERABILITY_FINDINGS_LABEL = "Vulnerability findings:"
SUMMARY_LICENSE_FINDINGS_LABEL = "License findings:"
VULNERABILITY_REMEDIATION_TEXT = "remediation: upgrade to a non-vulnerable version"
LICENSE_REMEDIATION_TEXT = "remediation: replace dependency or adjust policy"


def render_cli_summary(report: Report) -> str:
    """Render a human-readable summary from report data.

    Args:
        report: Report model with dependencies, vulnerabilities, and license findings.
    """
    severity_counts = {severity.value: 0 for severity in SEVERITY_ORDER}
    for vulnerability_finding in report.vulnerabilities:
        severity_counts[vulnerability_finding.severity.value] += 1

    license_violations = [item for item in report.licenses if item.policy_result == "violation"]
    license_warnings = [item for item in report.licenses if item.policy_result == "warn"]

    lines = [f"{SUMMARY_TOTAL_PACKAGES_LABEL}: {len(report.nodes)}", SUMMARY_VULNERABILITIES_LABEL]
    for severity in SEVERITY_ORDER:
        lines.append(f"  {severity.value}: {severity_counts[severity.value]}")

    lines.append(f"{SUMMARY_LICENSE_VIOLATIONS_LABEL}: {len(license_violations)}")
    lines.append(f"{SUMMARY_LICENSE_WARNINGS_LABEL}: {len(license_warnings)}")

    if report.vulnerabilities:
        lines.append(SUMMARY_VULNERABILITY_FINDINGS_LABEL)
        for vulnerability_finding in report.vulnerabilities:
            lines.append(
                f"  - {vulnerability_finding.package}=={vulnerability_finding.version} "
                f"{vulnerability_finding.vuln_id} ({vulnerability_finding.severity.value})"
            )
            for path in vulnerability_finding.paths:
                lines.append(f"    path: {' -> '.join(path)}")
            lines.append(f"    {VULNERABILITY_REMEDIATION_TEXT}")

    if license_violations or license_warnings:
        lines.append(SUMMARY_LICENSE_FINDINGS_LABEL)
        license_findings: list[LicenseFinding] = [*license_violations, *license_warnings]
        for license_finding in license_findings:
            lines.append(
                f"  - {license_finding.package}=={license_finding.version} {license_finding.policy_result} "
                f"({license_finding.normalized_spdx or 'unknown'})"
            )
            for path in license_finding.paths:
                lines.append(f"    path: {' -> '.join(path)}")
            if license_finding.policy_result == "violation":
                lines.append(f"    {LICENSE_REMEDIATION_TEXT}")

    return "\n".join(lines)


def write_json_report(report: Report, output_path: str) -> None:
    """Write the report JSON payload to disk.

    Args:
        report: Report model to serialize.
        output_path: Destination path for the JSON report file.
    """
    data = report.to_dict()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
