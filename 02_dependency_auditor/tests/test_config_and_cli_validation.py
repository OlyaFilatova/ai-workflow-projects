from __future__ import annotations

import io
from contextlib import redirect_stderr

import pytest

from auditpy.cli import build_parser
from auditpy.config import ScanConfig


def test_default_config() -> None:
    cfg = ScanConfig.create()
    assert cfg.policy == "no-gpl"
    assert cfg.fail_on == "high"
    assert cfg.cache_ttl_hours == 24
    assert cfg.verbose is False


def test_invalid_policy() -> None:
    with pytest.raises(ValueError, match="Unsupported policy"):
        ScanConfig.create(policy="allow-all")


def test_invalid_fail_threshold() -> None:
    with pytest.raises(ValueError, match="Unsupported fail threshold"):
        ScanConfig.create(fail_on="medium")


def test_invalid_ttl() -> None:
    with pytest.raises(ValueError, match="Cache TTL must be"):
        ScanConfig.create(cache_ttl_hours=0)


def test_cli_rejects_unknown_policy() -> None:
    parser = build_parser()
    err = io.StringIO()
    with redirect_stderr(err), pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["scan", "-r", "requirements.txt", "--policy", "invalid"])
    assert exc_info.value.code == 2
    assert "Only 'no-gpl' is currently supported" in err.getvalue()
