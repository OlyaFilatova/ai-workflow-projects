"""OpenAPI document to IR conversion and schema/type mapping."""

from __future__ import annotations

from typing import Any

from openapi_to_sdk.ir._mapper_common import (
    MappingContext,
    NameRegistry,
    UnsupportedSchemaError,
    as_dict,
    to_pascal_case,
)
from openapi_to_sdk.ir._operation_mapping import build_auth_schemes, build_operations
from openapi_to_sdk.ir._schema_mapping import build_schema_ir, map_schema_type
from openapi_to_sdk.ir.models import ApiIR

# Backward-compatible alias for internal callers that referenced the old private type.
_MappingContext = MappingContext


def build_api_ir(document: dict[str, Any]) -> ApiIR:
    """Build the full API IR from a resolved OpenAPI document.

    Args:
        document: OpenAPI document object with resolved references.
    """
    version = str(document.get("openapi", "3.1.0"))
    ctx = MappingContext(openapi_version=version, schema_name_map={})

    schema_registry = NameRegistry()
    operation_registry = NameRegistry()

    components = as_dict(document.get("components"))
    schema_sources = as_dict(components.get("schemas"))

    for raw_name in sorted(schema_sources):
        normalized = to_pascal_case(raw_name)
        ctx.schema_name_map[raw_name] = schema_registry.unique(normalized)

    schemas = [
        build_schema_ir(
            name=ctx.schema_name_map[raw_name],
            schema=as_dict(schema_sources[raw_name]),
            ctx=ctx,
        )
        for raw_name in sorted(schema_sources)
    ]

    auth_schemes = build_auth_schemes(components)
    operations = build_operations(document, ctx, operation_registry)

    return ApiIR(
        title=str(as_dict(document["info"])["title"]),
        version=str(as_dict(document["info"])["version"]),
        operations=operations,
        schemas=schemas,
        auth_schemes=auth_schemes,
    )


__all__ = ["UnsupportedSchemaError", "build_api_ir", "map_schema_type"]
