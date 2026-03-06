"""Schema-to-type and schema-to-IR mapping logic."""

from __future__ import annotations

from typing import Any

from openapi_to_sdk.ir._mapper_common import (
    MappingContext,
    NameRegistry,
    UnsupportedSchemaError,
    as_dict,
    as_list,
    to_pascal_case,
    to_snake_case,
)
from openapi_to_sdk.ir.models import FieldIR, SchemaIR


def map_schema_type(schema: dict[str, Any], *, ctx: MappingContext) -> str:
    if "$ref" in schema:
        return ref_to_type(str(schema["$ref"]), ctx)

    if "allOf" in schema:
        merged = merge_all_of(schema, ctx)
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
            variant_dict = as_dict(variant)
            if any(key in variant_dict for key in ("allOf", "oneOf", "anyOf", "discriminator")):
                raise UnsupportedSchemaError(
                    f"Nested composition inside {composition_key} is out of scope"
                )
            member_types.append(map_schema_type(variant_dict, ctx=ctx))

        deduped = list(dict.fromkeys(member_types))
        if len(deduped) < 2:
            raise UnsupportedSchemaError(f"Ambiguous {composition_key} composition")
        union = " | ".join(deduped)
        return apply_nullable(union, schema, ctx)

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and enum_values:
        literals = ", ".join(repr(item) for item in enum_values)
        return apply_nullable(f"Literal[{literals}]", schema, ctx)

    detected_type = schema_type(schema)
    if detected_type == "array":
        item_schema = as_dict(schema.get("items")) if isinstance(schema.get("items"), dict) else {}
        item_type = map_schema_type(item_schema, ctx=ctx) if item_schema else "Any"
        return apply_nullable(f"list[{item_type}]", schema, ctx)

    if detected_type == "object" or "properties" in schema or "additionalProperties" in schema:
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            value_type = map_schema_type(additional, ctx=ctx)
            return apply_nullable(f"dict[str, {value_type}]", schema, ctx)
        return apply_nullable("dict[str, Any]", schema, ctx)

    if detected_type == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            base = "datetime"
        elif fmt == "date":
            base = "date"
        elif fmt == "uuid":
            base = "UUID"
        else:
            base = "str"
        return apply_nullable(base, schema, ctx)

    if detected_type == "integer":
        return apply_nullable("int", schema, ctx)
    if detected_type == "number":
        return apply_nullable("float", schema, ctx)
    if detected_type == "boolean":
        return apply_nullable("bool", schema, ctx)

    return apply_nullable("Any", schema, ctx)


def build_schema_ir(name: str, schema: dict[str, Any], ctx: MappingContext) -> SchemaIR:
    if "allOf" in schema:
        schema = merge_all_of(schema, ctx)

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

    detected_type = schema_type(schema)
    if detected_type == "object" or "properties" in schema:
        required = {field_name for field_name in schema.get("required", []) if isinstance(field_name, str)}
        properties = as_dict(schema.get("properties"))

        fields: list[FieldIR] = []
        field_registry = NameRegistry()
        for raw_name in sorted(properties):
            prop_schema = as_dict(properties[raw_name])
            python_name = field_registry.unique(to_snake_case(raw_name))
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


def merge_all_of(schema: dict[str, Any], ctx: MappingContext) -> dict[str, Any]:
    blocks = schema.get("allOf")
    if not isinstance(blocks, list) or not blocks:
        raise UnsupportedSchemaError("allOf must be a non-empty list")

    merged: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for block in blocks:
        piece = as_dict(block)
        if "oneOf" in piece or "anyOf" in piece or "discriminator" in piece:
            raise UnsupportedSchemaError("Nested discriminator/union in allOf is out of scope")

        if "$ref" in piece:
            ref_to_type(str(piece["$ref"]), ctx)
            continue

        if not (
            schema_type(piece) == "object"
            or "properties" in piece
            or piece.get("type") in {None, "object"}
        ):
            raise UnsupportedSchemaError("allOf merge currently supports object-like schemas only")

        for prop_name, prop in as_dict(piece.get("properties")).items():
            as_dict(merged["properties"])[prop_name] = prop
        for required_name in piece.get("required", []):
            if isinstance(required_name, str) and required_name not in as_list(merged["required"]):
                as_list(merged["required"]).append(required_name)

        if "additionalProperties" in piece:
            merged["additionalProperties"] = piece["additionalProperties"]

    return merged


def ref_to_type(ref: str, ctx: MappingContext) -> str:
    if not ref.startswith("#/"):
        raise UnsupportedSchemaError(f"Only local refs are supported in MVP type mapping: {ref}")

    schema_name = ref.split("/")[-1]
    return ctx.schema_name_map.get(schema_name, to_pascal_case(schema_name))


def schema_type(schema: dict[str, Any]) -> str | None:
    value = schema.get("type")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if item != "null":
                return str(item)
    return None


def is_nullable(schema: dict[str, Any], ctx: MappingContext) -> bool:
    if bool(schema.get("nullable")) and ctx.openapi_version.startswith("3.0"):
        return True

    detected_type = schema.get("type")
    if isinstance(detected_type, list):
        return "null" in detected_type

    return False


def apply_nullable(type_hint: str, schema: dict[str, Any], ctx: MappingContext) -> str:
    if is_nullable(schema, ctx) and "None" not in type_hint:
        return f"{type_hint} | None"
    return type_hint
