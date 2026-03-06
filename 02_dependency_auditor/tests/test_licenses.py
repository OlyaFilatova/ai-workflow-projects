from __future__ import annotations

from auditpy.licenses import evaluate_licenses


def test_multi_license_or_expression() -> None:
    result = evaluate_licenses(
        [
            {
                "name": "example",
                "version": "1.0",
                "license": "MIT OR Apache-2.0",
                "classifiers": [],
            }
        ],
        {"example": [["root", "example"]]},
    )

    assert result.findings[0].normalized_spdx == "Apache-2.0 OR MIT"
    assert result.findings[0].policy_result == "allow"


def test_gpl_is_policy_violation_with_paths() -> None:
    result = evaluate_licenses(
        [
            {
                "name": "gplpkg",
                "version": "2.0",
                "license": "GPL-3.0",
                "classifiers": [],
            }
        ],
        {"gplpkg": [["root", "mid", "gplpkg"]]},
    )

    finding = result.findings[0]
    assert finding.policy_result == "violation"
    assert finding.paths == [["root", "mid", "gplpkg"]]


def test_unknown_license_is_warning() -> None:
    result = evaluate_licenses(
        [
            {
                "name": "unknownpkg",
                "version": "0.1",
                "license": "Custom internal license",
                "classifiers": [],
            }
        ],
        {},
    )

    assert result.findings[0].policy_result == "warn"
    assert result.findings[0].normalized_spdx is None
    assert len(result.warnings) == 1
