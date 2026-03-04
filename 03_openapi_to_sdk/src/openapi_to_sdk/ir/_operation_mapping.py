"""Operation and auth mapping from OpenAPI document sections."""

from __future__ import annotations

from typing import Any

from openapi_to_sdk.ir._mapper_common import (
    MappingContext,
    NameRegistry,
    as_dict,
    as_list,
    to_snake_case,
)
from openapi_to_sdk.ir._schema_mapping import map_schema_type
from openapi_to_sdk.ir.models import (
    AuthSchemeIR,
    OperationIR,
    ParameterIR,
    RequestBodyIR,
    ResponseIR,
)


def build_auth_schemes(components: dict[str, Any]) -> list[AuthSchemeIR]:
    schemes = as_dict(components.get("securitySchemes"))
    output: list[AuthSchemeIR] = []
    name_registry = NameRegistry()

    for raw_name in sorted(schemes):
        source = as_dict(schemes[raw_name])
        scheme_type = str(source.get("type", ""))
        python_name = name_registry.unique(to_snake_case(raw_name))

        if scheme_type == "apiKey":
            output.append(
                AuthSchemeIR(
                    name=raw_name,
                    python_name=python_name,
                    kind="apiKey",
                    location=str(source.get("in", "header")),
                )
            )
        elif scheme_type == "http" and str(source.get("scheme", "")).lower() == "bearer":
            output.append(
                AuthSchemeIR(
                    name=raw_name,
                    python_name=python_name,
                    kind="bearer",
                    scheme="bearer",
                )
            )

    return output


def build_operations(
    document: dict[str, Any],
    ctx: MappingContext,
    operation_registry: NameRegistry,
) -> list[OperationIR]:
    paths = as_dict(document.get("paths"))
    operations: list[OperationIR] = []
    global_security = document.get("security")

    for path in sorted(paths):
        path_item = as_dict(paths[path])
        path_level_params = as_list(path_item.get("parameters"))

        for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
            if method not in path_item:
                continue
            operation_source = as_dict(path_item[method])
            raw_operation_id = str(operation_source.get("operationId") or f"{method}_{path}")
            python_name = operation_registry.unique(to_snake_case(raw_operation_id))

            parameters = build_parameters(path_level_params + as_list(operation_source.get("parameters")), ctx)
            request_body = build_request_body(operation_source.get("requestBody"), ctx)
            responses = build_responses(operation_source.get("responses"), ctx)

            security = operation_source.get("security", global_security)
            auth_required = bool(security)

            operations.append(
                OperationIR(
                    operation_id=raw_operation_id,
                    python_name=python_name,
                    method=method.upper(),
                    path=path,
                    parameters=parameters,
                    request_body=request_body,
                    responses=responses,
                    auth_required=auth_required,
                )
            )

    return operations


def build_parameters(raw_parameters: list[Any], ctx: MappingContext) -> list[ParameterIR]:
    params: list[ParameterIR] = []
    name_registry = NameRegistry()

    for raw_param in raw_parameters:
        param = as_dict(raw_param)
        if "$ref" in param:
            continue
        raw_name = str(param.get("name", "param"))
        python_name = name_registry.unique(to_snake_case(raw_name))
        schema = as_dict(param.get("schema"))
        type_hint = map_schema_type(schema, ctx=ctx)
        required = bool(param.get("required", False))
        if not required and "None" not in type_hint:
            type_hint = f"{type_hint} | None"
        params.append(
            ParameterIR(
                name=raw_name,
                python_name=python_name,
                location=str(param.get("in", "query")),
                required=required,
                type_hint=type_hint,
            )
        )
    return params


def build_request_body(raw_request_body: Any, ctx: MappingContext) -> RequestBodyIR | None:
    if not isinstance(raw_request_body, dict):
        return None
    content = as_dict(raw_request_body.get("content"))
    if "application/json" not in content:
        return None

    media = as_dict(content["application/json"])
    schema = as_dict(media.get("schema"))
    return RequestBodyIR(
        required=bool(raw_request_body.get("required", False)),
        content_type="application/json",
        type_hint=map_schema_type(schema, ctx=ctx),
    )


def build_responses(raw_responses: Any, ctx: MappingContext) -> list[ResponseIR]:
    responses = as_dict(raw_responses)
    output: list[ResponseIR] = []

    for status in sorted(responses):
        source = as_dict(responses[status])
        content = as_dict(source.get("content"))
        media = as_dict(content.get("application/json")) if "application/json" in content else None
        schema = as_dict(media.get("schema")) if media is not None else None
        output.append(
            ResponseIR(
                status_code=status,
                content_type="application/json" if media is not None else None,
                type_hint=map_schema_type(schema, ctx=ctx) if schema is not None else None,
            )
        )

    return output
