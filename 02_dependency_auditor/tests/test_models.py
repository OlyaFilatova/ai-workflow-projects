from __future__ import annotations

import unittest

from auditpy.models import (
    DependencyEdge,
    LicenseFinding,
    PackageNode,
    Report,
    Severity,
    VulnerabilityFinding,
)


class ModelsTest(unittest.TestCase):
    def test_report_to_dict_is_deterministic(self) -> None:
        report = Report(
            python_version="3.12.0",
            timestamp="2026-03-04T00:00:00+00:00",
            nodes=[PackageNode(name="zlib", version="1.0"), PackageNode(name="abc", version="2.0")],
            edges=[DependencyEdge(source="zlib", target="abc", requirement=">=2")],
            vulnerabilities=[
                VulnerabilityFinding(
                    package="zlib",
                    version="1.0",
                    vuln_id="OSV-2",
                    severity=Severity.HIGH,
                    paths=[["root", "zlib"]],
                ),
                VulnerabilityFinding(
                    package="zlib",
                    version="1.0",
                    vuln_id="OSV-1",
                    severity=Severity.CRITICAL,
                    paths=[["root", "zlib"]],
                ),
            ],
            licenses=[
                LicenseFinding(
                    package="abc",
                    version="2.0",
                    declared="MIT",
                    normalized_spdx="MIT",
                    policy_name="no-gpl",
                    policy_result="allow",
                    paths=[["root", "abc"]],
                )
            ],
        )

        data = report.to_dict()
        self.assertEqual(data["metadata"]["python_version"], "3.12.0")
        self.assertEqual(data["dependency_graph"]["nodes"][0]["name"], "abc")
        self.assertEqual(data["vulnerabilities"][0]["id"], "OSV-1")
        self.assertEqual(data["license_findings"][0]["normalized_spdx"], "MIT")


if __name__ == "__main__":
    unittest.main()
