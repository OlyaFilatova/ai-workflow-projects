from __future__ import annotations

from pathlib import Path

from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir.models import ApiIR, SchemaIR


def test_generated_package_integrity(tmp_path: Path) -> None:
    """Test generated package integrity.

    Args:
        tmp_path: Argument value.
    """
    ir = ApiIR(
        title="Integrity API",
        version="1.0.0",
        schemas=[SchemaIR(name="Widget", python_name="Widget", kind="model", type_hint="Widget")],
    )

    render_sdk(ir, tmp_path)

    package_dir = tmp_path / "integrity_api"
    assert package_dir.exists()
    assert (package_dir / "__init__.py").exists()
    assert (package_dir / "models.py").exists()
    assert (package_dir / "client.py").exists()
    assert (package_dir / "py.typed").exists()

    init_source = (package_dir / "__init__.py").read_text(encoding="utf-8")
    assert "Client" in init_source
    assert "AsyncClient" in init_source
    assert "Widget" in init_source
