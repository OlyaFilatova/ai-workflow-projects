from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from auditpy.resolution import ResolutionFailure, _build_paths, resolve_dependencies


class ResolutionTest(unittest.TestCase):
    def test_missing_requirements_is_runtime_error(self) -> None:
        outcome = resolve_dependencies("/does/not/exist/requirements.txt")
        self.assertFalse(outcome.ok)
        assert isinstance(outcome.error, ResolutionFailure)
        self.assertEqual(outcome.error.category, "runtime")
        self.assertEqual(outcome.error.exit_code, 2)

    def test_build_paths_from_roots(self) -> None:
        adjacency = {
            "requests": {"urllib3", "certifi"},
            "urllib3": {"idna"},
            "certifi": set(),
            "idna": set(),
        }
        paths = _build_paths(["requests"], adjacency)
        self.assertIn(["requests"], paths["requests"])
        self.assertIn(["requests", "urllib3", "idna"], paths["idna"])

    @mock.patch("auditpy.resolution._collect_installed_distributions")
    @mock.patch("auditpy.resolution._pip_install_requirements")
    @mock.patch("auditpy.resolution._create_venv")
    def test_resolution_success_flow(self, _mock_venv, _mock_pip, mock_collect) -> None:
        mock_collect.return_value = [
            {"name": "requests", "version": "2.31.0", "requires": ["urllib3>=2", "idna>=3"]},
            {"name": "urllib3", "version": "2.2.0", "requires": []},
            {"name": "idna", "version": "3.7", "requires": []},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            req_file = Path(tmp_dir) / "requirements.txt"
            req_file.write_text("requests>=2\n", encoding="utf-8")
            outcome = resolve_dependencies(str(req_file))

        self.assertTrue(outcome.ok)
        self.assertEqual([node.name for node in outcome.nodes], ["idna", "requests", "urllib3"])
        self.assertIn("requests", outcome.dependency_paths)
        self.assertIn(["requests", "urllib3"], outcome.dependency_paths.get("urllib3", []))


if __name__ == "__main__":
    unittest.main()
