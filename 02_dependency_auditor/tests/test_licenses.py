from __future__ import annotations

import unittest

from auditpy.licenses import evaluate_licenses


class LicensePolicyTest(unittest.TestCase):
    def test_multi_license_or_expression(self) -> None:
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

        self.assertEqual(result.findings[0].normalized_spdx, "Apache-2.0 OR MIT")
        self.assertEqual(result.findings[0].policy_result, "allow")

    def test_gpl_is_policy_violation_with_paths(self) -> None:
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
        self.assertEqual(finding.policy_result, "violation")
        self.assertEqual(finding.paths, [["root", "mid", "gplpkg"]])

    def test_unknown_license_is_warning(self) -> None:
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

        self.assertEqual(result.findings[0].policy_result, "warn")
        self.assertIsNone(result.findings[0].normalized_spdx)
        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()
