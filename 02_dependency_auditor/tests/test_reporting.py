from __future__ import annotations

import unittest

from auditpy.models import LicenseFinding, PackageNode, Report, Severity, VulnerabilityFinding
from auditpy.reporting import render_cli_summary


class ReportingTest(unittest.TestCase):
    def test_summary_includes_paths_and_remediation(self) -> None:
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
        self.assertIn("path: requests -> urllib3", text)
        self.assertIn("remediation: upgrade to a non-vulnerable version", text)
        self.assertIn("remediation: replace dependency or adjust policy", text)


if __name__ == "__main__":
    unittest.main()
