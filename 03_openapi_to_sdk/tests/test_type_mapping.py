from __future__ import annotations

import pytest

from openapi_to_sdk.ir import UnsupportedSchemaError, build_api_ir


def test_type_mapping_required_optional_nullable_and_formats() -> None:
    """Test type mapping required optional nullable and formats."""
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Demo", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "integer"},
                        "nickname": {"type": "string"},
                        "born_at": {"type": "string", "format": "date-time"},
                        "score": {"type": ["number", "null"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                }
            }
        },
    }

    ir = build_api_ir(doc)
    user = ir.schemas[0]
    fields = {field.name: field for field in user.fields}

    assert user.kind == "model"
    assert fields["id"].type_hint == "int"
    assert fields["nickname"].type_hint == "str | None"
    assert fields["born_at"].type_hint == "datetime | None"
    assert fields["score"].type_hint == "float | None"
    assert fields["tags"].type_hint == "list[str] | None"


def test_type_mapping_enum_and_additional_properties() -> None:
    """Test type mapping enum and additional properties."""
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "Demo", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Status": {"type": "string", "enum": ["new", "done"]},
                "Labels": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            }
        },
    }

    ir = build_api_ir(doc)
    names = {schema.name: schema for schema in ir.schemas}

    assert names["Status"].type_hint == "Literal['new', 'done']"
    assert names["Labels"].additional_properties_type == "str"


def test_operation_and_schema_name_collisions_are_deterministic() -> None:
    """Test operation and schema name collisions are deterministic."""
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Naming", "version": "1.0.0"},
        "paths": {
            "/a": {"get": {"operationId": "get-pet", "responses": {"200": {"description": "ok"}}}},
            "/b": {"get": {"operationId": "get_pet", "responses": {"200": {"description": "ok"}}}},
        },
        "components": {
            "schemas": {
                "Pet": {"type": "object", "properties": {}},
                "pet": {"type": "object", "properties": {}},
            }
        },
    }

    ir = build_api_ir(doc)
    operation_names = [operation.python_name for operation in ir.operations]
    schema_names = [schema.name for schema in ir.schemas]

    assert operation_names == ["get_pet", "get_pet_2"]
    assert schema_names == ["Pet", "Pet_2"]


def test_allof_merge_and_simple_oneof_union() -> None:
    """Test allof merge and simple oneof union."""
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Compose", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Employee": {
                    "allOf": [
                        {
                            "type": "object",
                            "required": ["id"],
                            "properties": {"id": {"type": "integer"}},
                        },
                        {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        },
                    ]
                },
                "Identifier": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "integer"},
                    ]
                },
            }
        },
    }

    ir = build_api_ir(doc)
    schemas = {schema.name: schema for schema in ir.schemas}
    fields = {field.name: field for field in schemas["Employee"].fields}

    assert fields["id"].type_hint == "int"
    assert fields["name"].type_hint == "str | None"
    assert schemas["Identifier"].type_hint == "str | int"


def test_unsupported_discriminator_composition_fails() -> None:
    """Test unsupported discriminator composition fails."""
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Fail", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Animal": {
                    "oneOf": [{"$ref": "#/components/schemas/Cat"}],
                    "discriminator": {"propertyName": "type"},
                }
            }
        },
    }

    with pytest.raises(UnsupportedSchemaError, match="Discriminator"):
        build_api_ir(doc)
