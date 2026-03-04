from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from auditpy.models import PackageNode, Severity
from auditpy.vulnerabilities import scan_vulnerabilities


class VulnerabilityScanTest(unittest.TestCase):
    @mock.patch("auditpy.vulnerabilities._query_osv_batch")
    def test_cache_miss_then_hit(self, mock_query) -> None:
        mock_query.return_value = [{"vulns": [{"id": "OSV-123", "severity": [{"score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/9.8"}]}]}]
        nodes = [PackageNode(name="requests", version="2.31.0")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            first = scan_vulnerabilities(nodes, {"requests": [["requests"]]}, cache_dir=tmp_dir)
            second = scan_vulnerabilities(nodes, {"requests": [["requests"]]}, cache_dir=tmp_dir)

            cache_file = Path(tmp_dir) / "osv_cache.json"
            self.assertTrue(cache_file.exists())
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            self.assertIn("requests==2.31.0", cached)

        self.assertEqual(len(first.findings), 1)
        self.assertEqual(first.findings[0].severity, Severity.CRITICAL)
        self.assertEqual(len(second.findings), 1)
        self.assertEqual(mock_query.call_count, 1)

    @mock.patch("auditpy.vulnerabilities._query_osv_batch")
    def test_graceful_network_failure_with_stale_cache(self, mock_query) -> None:
        mock_query.side_effect = TimeoutError("timeout")
        nodes = [PackageNode(name="urllib3", version="2.2.0")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = Path(tmp_dir) / "osv_cache.json"
            cache_file.write_text(
                json.dumps(
                    {
                        "urllib3==2.2.0": {
                            "fetched_at": "2026-03-04T00:00:00+00:00",
                            "vulns": [{"id": "OSV-CACHED"}],
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = scan_vulnerabilities(
                nodes,
                {"urllib3": [["requests", "urllib3"]]},
                cache_dir=tmp_dir,
                cache_ttl_hours=0,
            )

        self.assertEqual(result.findings[0].vuln_id, "OSV-CACHED")
        self.assertEqual(result.findings[0].severity, Severity.MEDIUM)
        self.assertEqual(result.findings[0].paths, [["requests", "urllib3"]])
        self.assertEqual(len(result.warnings), 1)

    @mock.patch("auditpy.vulnerabilities._query_osv_batch")
    def test_timeout_without_cache_returns_warning_and_no_findings(self, mock_query) -> None:
        mock_query.side_effect = TimeoutError("timeout")
        nodes = [PackageNode(name="requests", version="2.31.0")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = scan_vulnerabilities(nodes, {"requests": [["requests"]]}, cache_dir=tmp_dir)

        self.assertEqual(result.findings, [])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("OSV query failed", result.warnings[0])

    @mock.patch("auditpy.vulnerabilities._query_osv_batch")
    def test_findings_order_is_deterministic(self, mock_query) -> None:
        mock_query.return_value = [
            {
                "vulns": [
                    {"id": "B", "severity": [{"score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/9.1"}]},
                    {"id": "A", "severity": [{"score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/7.5"}]},
                ]
            }
        ]
        nodes = [PackageNode(name="requests", version="2.31.0")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = scan_vulnerabilities(nodes, {"requests": [["requests"]]}, cache_dir=tmp_dir)

        self.assertEqual([item.vuln_id for item in result.findings], ["B", "A"])


if __name__ == "__main__":
    unittest.main()
