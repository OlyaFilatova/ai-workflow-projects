"""Policy evaluation helpers for scan fail conditions."""

from __future__ import annotations

from auditpy.models import Report, Severity


def threshold_violated(report: Report, *, fail_on: str) -> bool:
    severity_rank = {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
    }
    cutoff = Severity.HIGH if fail_on == "high" else Severity.CRITICAL

    vuln_violation = any(severity_rank[item.severity] >= severity_rank[cutoff] for item in report.vulnerabilities)
    license_violation = any(item.policy_result == "violation" for item in report.licenses)
    return vuln_violation or license_violation
