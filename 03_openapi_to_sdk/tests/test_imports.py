from openapi_to_sdk.cli.main import build_parser
from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir import ApiIR, build_api_ir
from openapi_to_sdk.parser.loader import load_openapi_document
from openapi_to_sdk.runtime.errors import ApiError


def test_import_smoke() -> None:
    """Test import smoke."""
    assert callable(build_parser)
    assert callable(render_sdk)
    assert callable(load_openapi_document)
    assert callable(build_api_ir)
    assert issubclass(ApiError, Exception)
    assert ApiIR(title="t", version="v").operations == []
