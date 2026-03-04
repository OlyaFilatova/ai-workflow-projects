from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from auditpy.parsing import RequirementsParseError, parse_requirements


class ParsingTest(unittest.TestCase):
    def test_parse_includes_markers_and_extras(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "more.txt").write_text(
                "urllib3>=2\n"
                "tomli; python_version < '3.11'\n",
                encoding="utf-8",
            )
            (root / "requirements.txt").write_text(
                "requests[socks]>=2.31\n"
                "-r more.txt\n",
                encoding="utf-8",
            )

            result = parse_requirements(str(root / "requirements.txt"))

        self.assertEqual([req.name for req in result.requirements], ["requests", "urllib3"])
        self.assertEqual(result.requirements[0].extras, ("socks",))
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("skipped by environment marker", result.warnings[0])

    def test_rejects_editable_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            req_file = Path(tmp_dir) / "requirements.txt"
            req_file.write_text("-e .\n", encoding="utf-8")
            with self.assertRaisesRegex(RequirementsParseError, "editable installs are unsupported"):
                parse_requirements(str(req_file))

    def test_rejects_direct_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            req_file = Path(tmp_dir) / "requirements.txt"
            req_file.write_text("pkg @ https://example.com/pkg.whl\n", encoding="utf-8")
            with self.assertRaisesRegex(
                RequirementsParseError,
                "direct URL/VCS dependencies are unsupported",
            ):
                parse_requirements(str(req_file))


if __name__ == "__main__":
    unittest.main()
