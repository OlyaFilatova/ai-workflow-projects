"""OpenAPI parser package."""

from openapi_to_sdk.parser.errors import OpenAPILoadError
from openapi_to_sdk.parser.loader import load_openapi_document

__all__ = ["OpenAPILoadError", "load_openapi_document"]
