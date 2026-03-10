from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from unittest.mock import MagicMock

from auditpy.cli import main
from auditpy.models import LicenseFinding, PackageNode, Severity, VulnerabilityFinding
from auditpy.resolution import ResolutionFailure, ResolutionOutcome
from auditpy.vulnerabilities import VulnerabilityScanResult


@mock.patch("auditpy.cli.evaluate_licenses")
@mock.patch("auditpy.cli.scan_vulnerabilities")
@mock.patch("auditpy.cli.resolve_dependencies")
def test_exit_code_zero_and_json_schema(
    mock_resolve: MagicMock,
    mock_vuln: MagicMock,
    mock_license: MagicMock,
) -> None:
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

        assert code == 0
        with open(json_path, encoding="utf-8") as fh:
            data = json.loads(fh.read())
        assert set(data.keys()) == {"metadata", "dependency_graph", "vulnerabilities", "license_findings"}
        assert "Total packages" in out.getvalue()


@mock.patch("auditpy.cli.evaluate_licenses")
@mock.patch("auditpy.cli.scan_vulnerabilities")
@mock.patch("auditpy.cli.resolve_dependencies")
def test_exit_code_one_on_threshold_violation(
    mock_resolve: MagicMock,
    mock_vuln: MagicMock,
    mock_license: MagicMock,
) -> None:
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

    assert code == 1
    assert "Vulnerabilities by severity" in out.getvalue()


@mock.patch("auditpy.cli.evaluate_licenses")
@mock.patch("auditpy.cli.scan_vulnerabilities")
@mock.patch("auditpy.cli.resolve_dependencies")
def test_exit_code_one_on_license_violation(
    mock_resolve: MagicMock,
    mock_vuln: MagicMock,
    mock_license: MagicMock,
) -> None:
    mock_resolve.return_value = ResolutionOutcome(
        nodes=[PackageNode(name="requests", version="2.31.0")],
        edges=[],
        dependency_paths={"gplpkg": [["requests", "gplpkg"]]},
        distributions=[],
    )
    mock_vuln.return_value = VulnerabilityScanResult(findings=[], warnings=[])
    mock_license.return_value = mock.Mock(
        findings=[
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
        warnings=[],
    )

    out = io.StringIO()
    with redirect_stdout(out):
        code = main(["scan", "-r", "requirements.txt", "--fail-on", "critical"])
    assert code == 1


@mock.patch("auditpy.cli.resolve_dependencies")
def test_exit_code_two_on_runtime_error(mock_resolve: MagicMock) -> None:
    mock_resolve.return_value = ResolutionOutcome(
        error=ResolutionFailure(category="runtime", message="boom", exit_code=2)
    )

    err = io.StringIO()
    with redirect_stderr(err):
        code = main(["scan", "-r", "requirements.txt"])

    assert code == 2
    assert "Runtime error" in err.getvalue()
