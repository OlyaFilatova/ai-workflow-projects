from __future__ import annotations

from auditpy.models import LicenseFinding, PackageNode, Report, Severity, VulnerabilityFinding
from auditpy.reporting import render_cli_summary


def test_summary_includes_paths_and_remediation() -> None:
    report = Report(
        python_version="3.13.2",
        nodes=[PackageNode(name="requests", version="2.31.0")],
        vulnerabilities=[
            VulnerabilityFinding(
                package="urllib3",
                version="2.2.0",
                vuln_id="OSV-1",
                severity=Severity.HIGH,
                paths=[["requests", "urllib3"]],
            )
        ],
        licenses=[
            LicenseFinding(
                package="gplpkg",
                version="1.0",
                declared="GPL-3.0",
                normalized_spdx="GPL-3.0-only",
                policy_name="no-gpl",
                policy_result="violation",
                paths=[["requests", "gplpkg"]],
            )
        ],
    )

    text = render_cli_summary(report)
    assert "path: requests -> urllib3" in text
    assert "remediation: upgrade to a non-vulnerable version" in text
    assert "remediation: replace dependency or adjust policy" in text
