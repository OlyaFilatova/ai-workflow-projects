from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir.models import ApiIR, FieldIR, SchemaIR


def _sample_ir() -> ApiIR:
    """Build a representative API IR fixture for renderer tests."""
    user_schema = SchemaIR(
        name="User",
        python_name="User",
        kind="model",
        type_hint="User",
        fields=[
            FieldIR(name="id", python_name="id", type_hint="int", required=True),
            FieldIR(name="class", python_name="class_", type_hint="str | None", required=False),
        ],
    )
    status_schema = SchemaIR(
        name="Status",
        python_name="Status",
        kind="enum",
        type_hint="Literal['new', 'done']",
    )
    return ApiIR(title="Demo API", version="1.0.0", schemas=[status_schema, user_schema])


def _normalize(source: str) -> str:
    """Normalize source text for deterministic snapshot comparisons.

    Args:
        source: Input source text to normalize.
    """
    lines = [line.rstrip() for line in source.splitlines()]
    compact: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        compact.append(line)
        previous_blank = is_blank
    return "\n".join(compact).strip() + "\n"


def test_template_render_generates_valid_python(tmp_path: Path) -> None:
    """Test template render generates valid python.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    render_sdk(_sample_ir(), tmp_path)

    models_file = tmp_path / "demo_api" / "models.py"
    package_init = tmp_path / "demo_api" / "__init__.py"
    client_file = tmp_path / "demo_api" / "client.py"

    assert models_file.exists()
    assert package_init.exists()
    assert client_file.exists()

    ast.parse(models_file.read_text(encoding="utf-8"))
    ast.parse(package_init.read_text(encoding="utf-8"))
    ast.parse(client_file.read_text(encoding="utf-8"))


def test_template_render_is_deterministic(tmp_path: Path) -> None:
    """Test template render is deterministic.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    ir = _sample_ir()

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    render_sdk(ir, out_a)
    render_sdk(ir, out_b)

    first = (out_a / "demo_api" / "models.py").read_text(encoding="utf-8")
    second = (out_b / "demo_api" / "models.py").read_text(encoding="utf-8")

    assert first == second


def test_template_render_matches_golden_snapshot(tmp_path: Path) -> None:
    """Test template render matches golden snapshot.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    render_sdk(_sample_ir(), tmp_path)

    generated = (tmp_path / "demo_api" / "models.py").read_text(encoding="utf-8")
    golden = (Path(__file__).parent / "golden" / "models.py").read_text(encoding="utf-8")

    assert _normalize(generated) == _normalize(golden)


def test_client_template_render_matches_golden_snapshot(tmp_path: Path) -> None:
    """Test client template render matches golden snapshot.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    render_sdk(_sample_ir(), tmp_path)

    generated = (tmp_path / "demo_api" / "client.py").read_text(encoding="utf-8")
    golden = (Path(__file__).parent / "golden" / "client.py").read_text(encoding="utf-8")

    assert _normalize(generated) == _normalize(golden)


def test_generated_package_import_smoke_when_pydantic_available(tmp_path: Path) -> None:
    """Test generated package import smoke when pydantic available.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    if importlib.util.find_spec("pydantic") is None:
        pytest.skip("pydantic not installed in this environment")

    render_sdk(_sample_ir(), tmp_path)

    sys.path.insert(0, str(tmp_path))
    try:
        module = __import__("demo_api")
    finally:
        sys.path.pop(0)

    assert hasattr(module, "User")


def test_template_render_renders_stdlib_imports_by_module(tmp_path: Path) -> None:
    """Test stdlib imports render as module-to-symbol mappings.

    Args:
        tmp_path: Temporary directory path provided by pytest.
    """
    dated_schema = SchemaIR(
        name="AuditRecord",
        python_name="AuditRecord",
        kind="model",
        type_hint="AuditRecord",
        fields=[
            FieldIR(name="created_at", python_name="created_at", type_hint="datetime", required=True),
            FieldIR(name="created_on", python_name="created_on", type_hint="date", required=True),
            FieldIR(name="event_id", python_name="event_id", type_hint="UUID", required=True),
        ],
    )
    ir = ApiIR(title="Dates API", version="1.0.0", schemas=[dated_schema])

    render_sdk(ir, tmp_path)

    generated = (tmp_path / "dates_api" / "models.py").read_text(encoding="utf-8")

    assert "from datetime import date, datetime" in generated
    assert "from uuid import UUID" in generated
