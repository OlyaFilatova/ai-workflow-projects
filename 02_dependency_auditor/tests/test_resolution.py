from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from auditpy.resolution import ResolutionFailure, _build_paths, resolve_dependencies


def test_missing_requirements_is_runtime_error() -> None:
    outcome = resolve_dependencies("/does/not/exist/requirements.txt")
    assert outcome.ok is False
    assert isinstance(outcome.error, ResolutionFailure)
    assert outcome.error.category == "runtime"
    assert outcome.error.exit_code == 2


def test_build_paths_from_roots() -> None:
    adjacency = {
        "requests": {"urllib3", "certifi"},
        "urllib3": {"idna"},
        "certifi": set(),
        "idna": set(),
    }
    paths = _build_paths(["requests"], adjacency)
    assert ["requests"] in paths["requests"]
    assert ["requests", "urllib3", "idna"] in paths["idna"]


@mock.patch("auditpy.resolution._collect_installed_distributions")
@mock.patch("auditpy.resolution._pip_install_requirements")
@mock.patch("auditpy.resolution._create_venv")
def test_resolution_success_flow(
    _mock_venv: MagicMock,
    _mock_pip: MagicMock,
    mock_collect: MagicMock,
) -> None:
    mock_collect.return_value = [
        {"name": "requests", "version": "2.31.0", "requires": ["urllib3>=2", "idna>=3"]},
        {"name": "urllib3", "version": "2.2.0", "requires": []},
        {"name": "idna", "version": "3.7", "requires": []},
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        req_file = Path(tmp_dir) / "requirements.txt"
        req_file.write_text("requests>=2\n", encoding="utf-8")
        outcome = resolve_dependencies(str(req_file))

    assert outcome.ok is True
    assert [node.name for node in outcome.nodes] == ["idna", "requests", "urllib3"]
    assert "requests" in outcome.dependency_paths
    assert ["requests", "urllib3"] in outcome.dependency_paths.get("urllib3", [])


@mock.patch("auditpy.resolution._pip_install_requirements")
@mock.patch("auditpy.resolution._create_venv")
def test_pip_install_failure_is_runtime_error(_mock_venv: MagicMock, mock_pip: MagicMock) -> None:
    mock_pip.side_effect = RuntimeError("Dependency resolution failed: network unavailable")

    with tempfile.TemporaryDirectory() as tmp_dir:
        req_file = Path(tmp_dir) / "requirements.txt"
        req_file.write_text("requests>=2\n", encoding="utf-8")
        outcome = resolve_dependencies(str(req_file))

    assert outcome.ok is False
    assert outcome.error is not None
    assert outcome.error.category == "runtime"
    assert "network unavailable" in outcome.error.message
