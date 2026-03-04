from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from auditpy.cli import main
from auditpy.models import LicenseFinding, PackageNode, Severity, VulnerabilityFinding
from auditpy.resolution import ResolutionFailure, ResolutionOutcome
from auditpy.vulnerabilities import VulnerabilityScanResult


class CliReportingTest(unittest.TestCase):
    @mock.patch("auditpy.cli.evaluate_licenses")
    @mock.patch("auditpy.cli.scan_vulnerabilities")
    @mock.patch("auditpy.cli.resolve_dependencies")
    def test_exit_code_zero_and_json_schema(self, mock_resolve, mock_vuln, mock_license) -> None:
        mock_resolve.return_value = ResolutionOutcome(
            nodes=[PackageNode(name="requests", version="2.31.0")],
            edges=[],
            dependency_paths={"requests": [["requests"]]},
            distributions=[{"name": "requests", "version": "2.31.0", "license": "MIT", "classifiers": []}],
        )
        mock_vuln.return_value = VulnerabilityScanResult(findings=[], warnings=[])
        mock_license.return_value = mock.Mock(
            findings=[
                LicenseFinding(
                    package="requests",
                    version="2.31.0",
                    declared="MIT",
                    normalized_spdx="MIT",
                    policy_name="no-gpl",
                    policy_result="allow",
                    paths=[["requests"]],
                )
            ],
            warnings=[],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = f"{tmp_dir}/report.json"
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["scan", "-r", "requirements.txt", "--json", json_path])

            self.assertEqual(code, 0)
            with open(json_path, encoding="utf-8") as fh:
                data = json.loads(fh.read())
            self.assertEqual(set(data.keys()), {"metadata", "dependency_graph", "vulnerabilities", "license_findings"})
            self.assertIn("Total packages", out.getvalue())

    @mock.patch("auditpy.cli.evaluate_licenses")
    @mock.patch("auditpy.cli.scan_vulnerabilities")
    @mock.patch("auditpy.cli.resolve_dependencies")
    def test_exit_code_one_on_threshold_violation(self, mock_resolve, mock_vuln, mock_license) -> None:
        mock_resolve.return_value = ResolutionOutcome(
            nodes=[PackageNode(name="requests", version="2.31.0")],
            edges=[],
            dependency_paths={"requests": [["requests"]]},
            distributions=[],
        )
        mock_vuln.return_value = VulnerabilityScanResult(
            findings=[
                VulnerabilityFinding(
                    package="requests",
                    version="2.31.0",
                    vuln_id="OSV-1",
                    severity=Severity.HIGH,
                    paths=[["requests"]],
                )
            ],
            warnings=[],
        )
        mock_license.return_value = mock.Mock(findings=[], warnings=[])

        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["scan", "-r", "requirements.txt", "--fail-on", "high"])

        self.assertEqual(code, 1)
        self.assertIn("Vulnerabilities by severity", out.getvalue())

    @mock.patch("auditpy.cli.resolve_dependencies")
    def test_exit_code_two_on_runtime_error(self, mock_resolve) -> None:
        mock_resolve.return_value = ResolutionOutcome(
            error=ResolutionFailure(category="runtime", message="boom", exit_code=2)
        )

        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["scan", "-r", "requirements.txt"])

        self.assertEqual(code, 2)
        self.assertIn("Runtime error", err.getvalue())


if __name__ == "__main__":
    unittest.main()
