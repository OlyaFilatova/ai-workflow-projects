"""OpenAPI document to IR conversion and schema/type mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from openapi_to_sdk.ir.models import (
    ApiIR,
    AuthSchemeIR,
    FieldIR,
    OperationIR,
    ParameterIR,
    RequestBodyIR,
    ResponseIR,
    SchemaIR,
)


class UnsupportedSchemaError(ValueError):
    """Raised when schema features are outside the supported MVP subset."""


@dataclass(slots=True)
class _MappingContext:
    openapi_version: str
    schema_name_map: dict[str, str]


class _NameRegistry:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def unique(self, base: str) -> str:
        clean = base or "item"
        if clean not in self._used:
            self._used.add(clean)
            return clean

        index = 2
        while True:
            candidate = f"{clean}_{index}"
            if candidate not in self._used:
                self._used.add(candidate)
                return candidate
            index += 1


def build_api_ir(document: dict[str, Any]) -> ApiIR:
    version = str(document.get("openapi", "3.1.0"))
    ctx = _MappingContext(openapi_version=version, schema_name_map={})

    schema_registry = _NameRegistry()
    operation_registry = _NameRegistry()

    components = _as_dict(document.get("components"))
    schema_sources = _as_dict(components.get("schemas"))

    for raw_name in sorted(schema_sources):
        normalized = _to_pascal_case(raw_name)
        ctx.schema_name_map[raw_name] = schema_registry.unique(normalized)

    schemas: list[SchemaIR] = []
    for raw_name in sorted(schema_sources):
        normalized = ctx.schema_name_map[raw_name]
        schema_ir = _build_schema_ir(name=normalized, schema=_as_dict(schema_sources[raw_name]), ctx=ctx)
        schemas.append(schema_ir)

    auth_schemes = _build_auth_schemes(components)
    operations = _build_operations(document, ctx, operation_registry)

    return ApiIR(
        title=str(_as_dict(document["info"])["title"]),
        version=str(_as_dict(document["info"])["version"]),
        operations=operations,
        schemas=schemas,
        auth_schemes=auth_schemes,
    )


def map_schema_type(schema: dict[str, Any], *, ctx: _MappingContext) -> str:
    if "$ref" in schema:
        return _ref_to_type(str(schema["$ref"]), ctx)

    if "allOf" in schema:
        merged = _merge_all_of(schema, ctx)
        return map_schema_type(merged, ctx=ctx)

    composition_key = "oneOf" if "oneOf" in schema else "anyOf" if "anyOf" in schema else None
    if composition_key is not None:
        if "discriminator" in schema:
            raise UnsupportedSchemaError("Discriminator-based oneOf/anyOf is out of scope")

        variants = schema.get(composition_key)
        if not isinstance(variants, list) or not variants:
            raise UnsupportedSchemaError(f"{composition_key} must contain variants")

        member_types: list[str] = []
        for variant in variants:
            variant_dict = _as_dict(variant)
            if any(key in variant_dict for key in ("allOf", "oneOf", "anyOf", "discriminator")):
                raise UnsupportedSchemaError(
                    f"Nested composition inside {composition_key} is out of scope"
                )
            member_types.append(map_schema_type(variant_dict, ctx=ctx))

        deduped = list(dict.fromkeys(member_types))
        if len(deduped) < 2:
            raise UnsupportedSchemaError(f"Ambiguous {composition_key} composition")
        union = " | ".join(deduped)
        return _apply_nullable(union, schema, ctx)

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and enum_values:
        literals = ", ".join(repr(item) for item in enum_values)
        return _apply_nullable(f"Literal[{literals}]", schema, ctx)

    schema_type = _schema_type(schema)
    if schema_type == "array":
        item_schema = _as_dict(schema.get("items")) if isinstance(schema.get("items"), dict) else {}
        item_type = map_schema_type(item_schema, ctx=ctx) if item_schema else "Any"
        return _apply_nullable(f"list[{item_type}]", schema, ctx)

    if schema_type == "object" or "properties" in schema or "additionalProperties" in schema:
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            value_type = map_schema_type(additional, ctx=ctx)
            return _apply_nullable(f"dict[str, {value_type}]", schema, ctx)
        return _apply_nullable("dict[str, Any]", schema, ctx)

    if schema_type == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            base = "datetime"
        elif fmt == "date":
            base = "date"
        elif fmt == "uuid":
            base = "UUID"
        else:
            base = "str"
        return _apply_nullable(base, schema, ctx)

    if schema_type == "integer":
        return _apply_nullable("int", schema, ctx)
    if schema_type == "number":
        return _apply_nullable("float", schema, ctx)
    if schema_type == "boolean":
        return _apply_nullable("bool", schema, ctx)

    return _apply_nullable("Any", schema, ctx)


def _build_schema_ir(name: str, schema: dict[str, Any], ctx: _MappingContext) -> SchemaIR:
    if "allOf" in schema:
        schema = _merge_all_of(schema, ctx)

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and enum_values:
        return SchemaIR(
            name=name,
            python_name=name,
            kind="enum",
            type_hint=map_schema_type(schema, ctx=ctx),
            enum_values=[str(item) for item in enum_values],
        )

    if "$ref" in schema:
        return SchemaIR(
            name=name,
            python_name=name,
            kind="alias",
            type_hint=map_schema_type(schema, ctx=ctx),
        )

    schema_type = _schema_type(schema)
    if schema_type == "object" or "properties" in schema:
        required = {
            field_name
            for field_name in schema.get("required", [])
            if isinstance(field_name, str)
        }
        properties = _as_dict(schema.get("properties"))

        fields: list[FieldIR] = []
        field_registry = _NameRegistry()
        for raw_name in sorted(properties):
            prop_schema = _as_dict(properties[raw_name])
            python_name = field_registry.unique(_to_snake_case(raw_name))
            field_type = map_schema_type(prop_schema, ctx=ctx)
            is_required = raw_name in required
            if not is_required and "None" not in field_type:
                field_type = f"{field_type} | None"
            fields.append(
                FieldIR(
                    name=raw_name,
                    python_name=python_name,
                    type_hint=field_type,
                    required=is_required,
                )
            )

        additional_properties_type: str | None = None
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            additional_properties_type = map_schema_type(additional, ctx=ctx)
        elif additional is True:
            additional_properties_type = "Any"

        return SchemaIR(
            name=name,
            python_name=name,
            kind="model",
            type_hint=name,
            fields=fields,
            additional_properties_type=additional_properties_type,
        )

    return SchemaIR(
        name=name,
        python_name=name,
        kind="alias",
        type_hint=map_schema_type(schema, ctx=ctx),
    )


def _build_auth_schemes(components: dict[str, Any]) -> list[AuthSchemeIR]:
    schemes = _as_dict(components.get("securitySchemes"))
    output: list[AuthSchemeIR] = []
    name_registry = _NameRegistry()

    for raw_name in sorted(schemes):
        source = _as_dict(schemes[raw_name])
        scheme_type = str(source.get("type", ""))
        python_name = name_registry.unique(_to_snake_case(raw_name))

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


def _build_operations(
    document: dict[str, Any],
    ctx: _MappingContext,
    operation_registry: _NameRegistry,
) -> list[OperationIR]:
    paths = _as_dict(document.get("paths"))
    operations: list[OperationIR] = []
    global_security = document.get("security")

    for path in sorted(paths):
        path_item = _as_dict(paths[path])
        path_level_params = _as_list(path_item.get("parameters"))

        for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
            if method not in path_item:
                continue
            operation_source = _as_dict(path_item[method])
            raw_operation_id = str(operation_source.get("operationId") or f"{method}_{path}")
            python_name = operation_registry.unique(_to_snake_case(raw_operation_id))

            parameters = _build_parameters(path_level_params + _as_list(operation_source.get("parameters")), ctx)
            request_body = _build_request_body(operation_source.get("requestBody"), ctx)
            responses = _build_responses(operation_source.get("responses"), ctx)

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


def _build_parameters(raw_parameters: list[Any], ctx: _MappingContext) -> list[ParameterIR]:
    params: list[ParameterIR] = []
    name_registry = _NameRegistry()

    for raw_param in raw_parameters:
        param = _as_dict(raw_param)
        if "$ref" in param:
            continue
        raw_name = str(param.get("name", "param"))
        python_name = name_registry.unique(_to_snake_case(raw_name))
        schema = _as_dict(param.get("schema"))
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


def _build_request_body(raw_request_body: Any, ctx: _MappingContext) -> RequestBodyIR | None:
    if not isinstance(raw_request_body, dict):
        return None
    content = _as_dict(raw_request_body.get("content"))
    if "application/json" not in content:
        return None

    media = _as_dict(content["application/json"])
    schema = _as_dict(media.get("schema"))
    return RequestBodyIR(
        required=bool(raw_request_body.get("required", False)),
        content_type="application/json",
        type_hint=map_schema_type(schema, ctx=ctx),
    )


def _build_responses(raw_responses: Any, ctx: _MappingContext) -> list[ResponseIR]:
    responses = _as_dict(raw_responses)
    output: list[ResponseIR] = []

    for status in sorted(responses):
        source = _as_dict(responses[status])
        content = _as_dict(source.get("content"))
        media = _as_dict(content.get("application/json")) if "application/json" in content else None
        schema = _as_dict(media.get("schema")) if media is not None else None
        output.append(
            ResponseIR(
                status_code=status,
                content_type="application/json" if media is not None else None,
                type_hint=map_schema_type(schema, ctx=ctx) if schema is not None else None,
            )
        )

    return output


def _merge_all_of(schema: dict[str, Any], ctx: _MappingContext) -> dict[str, Any]:
    blocks = schema.get("allOf")
    if not isinstance(blocks, list) or not blocks:
        raise UnsupportedSchemaError("allOf must be a non-empty list")

    merged: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for block in blocks:
        piece = _as_dict(block)
        if "oneOf" in piece or "anyOf" in piece or "discriminator" in piece:
            raise UnsupportedSchemaError("Nested discriminator/union in allOf is out of scope")

        if "$ref" in piece:
            ref_type = _ref_to_type(str(piece["$ref"]), ctx)
            if ref_type in ctx.schema_name_map.values():
                # Keep typed linkage; rendering can map this reference.
                merged.setdefault("x_ref_parts", []).append(ref_type)
            continue

        if not (
            _schema_type(piece) == "object"
            or "properties" in piece
            or piece.get("type") in {None, "object"}
        ):
            raise UnsupportedSchemaError("allOf merge currently supports object-like schemas only")

        for name, prop in _as_dict(piece.get("properties")).items():
            _as_dict(merged["properties"])[name] = prop
        for required_name in piece.get("required", []):
            if isinstance(required_name, str) and required_name not in _as_list(merged["required"]):
                _as_list(merged["required"]).append(required_name)

        if "additionalProperties" in piece:
            merged["additionalProperties"] = piece["additionalProperties"]

    return merged


def _ref_to_type(ref: str, ctx: _MappingContext) -> str:
    if not ref.startswith("#/"):
        raise UnsupportedSchemaError(f"Only local refs are supported in MVP type mapping: {ref}")

    schema_name = ref.split("/")[-1]
    return ctx.schema_name_map.get(schema_name, _to_pascal_case(schema_name))


def _schema_type(schema: dict[str, Any]) -> str | None:
    value = schema.get("type")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if item != "null":
                return str(item)
    return None


def _is_nullable(schema: dict[str, Any], ctx: _MappingContext) -> bool:
    if bool(schema.get("nullable")) and ctx.openapi_version.startswith("3.0"):
        return True

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return "null" in schema_type

    return False


def _apply_nullable(type_hint: str, schema: dict[str, Any], ctx: _MappingContext) -> str:
    if _is_nullable(schema, ctx) and "None" not in type_hint:
        return f"{type_hint} | None"
    return type_hint


def _to_snake_case(raw: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")
    if not base:
        return "item"
    base = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", base)
    snake = base.lower()
    if snake[0].isdigit():
        return f"n_{snake}"
    return snake


def _to_pascal_case(raw: str) -> str:
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", raw) if token]
    if not tokens:
        return "Model"
    pascal = "".join(token[:1].upper() + token[1:] for token in tokens)
    if pascal[0].isdigit():
        return f"Model{pascal}"
    return pascal


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
