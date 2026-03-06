from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from auditpy.parsing import RequirementsParseError, parse_requirements


def test_parse_includes_markers_and_extras() -> None:
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

    assert [req.name for req in result.requirements] == ["requests", "urllib3"]
    assert result.requirements[0].extras == ("socks",)
    assert len(result.warnings) == 1
    assert "skipped by environment marker" in result.warnings[0]


def test_rejects_editable_install() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        req_file = Path(tmp_dir) / "requirements.txt"
        req_file.write_text("-e .\n", encoding="utf-8")
        with pytest.raises(RequirementsParseError, match="editable installs are unsupported"):
            parse_requirements(str(req_file))


def test_rejects_direct_url() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        req_file = Path(tmp_dir) / "requirements.txt"
        req_file.write_text("pkg @ https://example.com/pkg.whl\n", encoding="utf-8")
        with pytest.raises(RequirementsParseError, match="direct URL/VCS dependencies are unsupported"):
            parse_requirements(str(req_file))


def test_malformed_requirement_has_file_and_line() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        req_file = Path(tmp_dir) / "requirements.txt"
        req_file.write_text("bad requirement @@@\n", encoding="utf-8")

        with pytest.raises(RequirementsParseError, match="invalid requirement") as exc_info:
            parse_requirements(str(req_file))

    assert "requirements.txt:1" in str(exc_info.value)
