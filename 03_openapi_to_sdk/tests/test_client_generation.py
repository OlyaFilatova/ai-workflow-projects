from __future__ import annotations

from pathlib import Path

from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir.models import ApiIR, OperationIR, ResponseIR, SchemaIR


def test_generated_client_contains_operation_methods(tmp_path: Path) -> None:
    """Test generated client contains operation methods.

    Args:
        tmp_path: Argument value.
    """
    ir = ApiIR(
        title="Pets",
        version="1.0.0",
        schemas=[SchemaIR(name="Pet", python_name="Pet", kind="model", type_hint="Pet")],
        operations=[
            OperationIR(
                operation_id="getPet",
                python_name="get_pet",
                method="GET",
                path="/pets/{pet_id}",
                responses=[ResponseIR(status_code="200", content_type="application/json", type_hint="Pet")],
            )
        ],
    )

    render_sdk(ir, tmp_path)

    client_source = (tmp_path / "pets" / "client.py").read_text(encoding="utf-8")
    assert "def get_pet(" in client_source
    assert 'method="GET"' in client_source
    assert 'path="/pets/{pet_id}"' in client_source
    assert "response_model=Pet" in client_source
    assert "class AsyncClient" in client_source
