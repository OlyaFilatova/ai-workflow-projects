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

SUPPORTED_HTTP_METHODS = ["get", "post", "put", "patch", "delete", "options", "head"]
JSON_MEDIA_TYPE = "application/json"
DEFAULT_PARAM_NAME = "param"
DEFAULT_PARAM_LOCATION = "query"
DEFAULT_APIKEY_LOCATION = "header"
DEFAULT_OPERATION_ID_TEMPLATE = "{method}_{path}"


def build_auth_schemes(components: dict[str, Any]) -> list[AuthSchemeIR]:
    """Build auth-scheme IR objects from OpenAPI components.

    Args:
        components: OpenAPI `components` object.
    """
    raw_schemes = as_dict(components.get("securitySchemes"))
    auth_schemes: list[AuthSchemeIR] = []
    name_registry = NameRegistry()

    for raw_name in sorted(raw_schemes):
        scheme_data = as_dict(raw_schemes[raw_name])
        scheme_type = str(scheme_data.get("type", ""))
        python_name = name_registry.unique(to_snake_case(raw_name))

        if scheme_type == "apiKey":
            auth_schemes.append(
                AuthSchemeIR(
                    name=raw_name,
                    python_name=python_name,
                    kind="apiKey",
                    location=str(scheme_data.get("in", DEFAULT_APIKEY_LOCATION)),
                )
            )
        elif scheme_type == "http" and str(scheme_data.get("scheme", "")).lower() == "bearer":
            auth_schemes.append(
                AuthSchemeIR(
                    name=raw_name,
                    python_name=python_name,
                    kind="bearer",
                    scheme="bearer",
                )
            )

    return auth_schemes


def build_operations(
    document: dict[str, Any],
    ctx: MappingContext,
    operation_registry: NameRegistry,
) -> list[OperationIR]:
    """Build operation IR objects from OpenAPI paths.

    Args:
        document: Fully resolved OpenAPI document.
        ctx: Shared mapping context.
        operation_registry: Registry for unique operation method names.
    """
    paths = as_dict(document.get("paths"))
    operations: list[OperationIR] = []
    global_security = document.get("security")

    for path in sorted(paths):
        path_item = as_dict(paths[path])
        path_level_params = as_list(path_item.get("parameters"))

        for method in SUPPORTED_HTTP_METHODS:
            if method not in path_item:
                continue
            operation_source = as_dict(path_item[method])
            default_operation_id = DEFAULT_OPERATION_ID_TEMPLATE.format(method=method, path=path)
            raw_operation_id = str(operation_source.get("operationId") or default_operation_id)
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
    """Build parameter IR objects from OpenAPI parameter definitions.

    Args:
        raw_parameters: Merged list of path-level and operation-level parameters.
        ctx: Shared mapping context.
    """
    params: list[ParameterIR] = []
    name_registry = NameRegistry()

    for raw_param in raw_parameters:
        param = as_dict(raw_param)
        if "$ref" in param:
            continue
        raw_name = str(param.get("name", DEFAULT_PARAM_NAME))
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
                location=str(param.get("in", DEFAULT_PARAM_LOCATION)),
                required=required,
                type_hint=type_hint,
            )
        )
    return params


def build_request_body(raw_request_body: Any, ctx: MappingContext) -> RequestBodyIR | None:
    """Build request-body IR for JSON request bodies.

    Args:
        raw_request_body: OpenAPI requestBody object.
        ctx: Shared mapping context.
    """
    if not isinstance(raw_request_body, dict):
        return None
    content = as_dict(raw_request_body.get("content"))
    if JSON_MEDIA_TYPE not in content:
        return None

    media = as_dict(content[JSON_MEDIA_TYPE])
    schema = as_dict(media.get("schema"))
    return RequestBodyIR(
        required=bool(raw_request_body.get("required", False)),
        content_type=JSON_MEDIA_TYPE,
        type_hint=map_schema_type(schema, ctx=ctx),
    )


def build_responses(raw_responses: Any, ctx: MappingContext) -> list[ResponseIR]:
    """Build response IR objects from OpenAPI responses.

    Args:
        raw_responses: OpenAPI responses object.
        ctx: Shared mapping context.
    """
    response_map = as_dict(raw_responses)
    response_models: list[ResponseIR] = []

    for status in sorted(response_map):
        response_data = as_dict(response_map[status])
        content = as_dict(response_data.get("content"))
        media = as_dict(content.get(JSON_MEDIA_TYPE)) if JSON_MEDIA_TYPE in content else None
        schema = as_dict(media.get("schema")) if media is not None else None
        response_models.append(
            ResponseIR(
                status_code=status,
                content_type=JSON_MEDIA_TYPE if media is not None else None,
                type_hint=map_schema_type(schema, ctx=ctx) if schema is not None else None,
            )
        )

    return response_models
