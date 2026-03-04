from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr

from auditpy.cli import build_parser
from auditpy.config import ScanConfig


class ConfigValidationTest(unittest.TestCase):
    def test_default_config(self) -> None:
        cfg = ScanConfig.create()
        self.assertEqual(cfg.policy, "no-gpl")
        self.assertEqual(cfg.fail_on, "high")
        self.assertEqual(cfg.cache_ttl_hours, 24)
        self.assertFalse(cfg.verbose)

    def test_invalid_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported policy"):
            ScanConfig.create(policy="allow-all")

    def test_invalid_fail_threshold(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported fail threshold"):
            ScanConfig.create(fail_on="medium")

    def test_invalid_ttl(self) -> None:
        with self.assertRaisesRegex(ValueError, "Cache TTL must be"):
            ScanConfig.create(cache_ttl_hours=0)


class CliValidationTest(unittest.TestCase):
    def test_cli_rejects_unknown_policy(self) -> None:
        parser = build_parser()
        err = io.StringIO()
        with redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
            parser.parse_args(["scan", "-r", "requirements.txt", "--policy", "invalid"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("Only 'no-gpl' is currently supported", err.getvalue())


if __name__ == "__main__":
    unittest.main()
