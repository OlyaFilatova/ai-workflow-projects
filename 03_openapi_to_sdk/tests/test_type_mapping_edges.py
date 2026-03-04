from __future__ import annotations

import pytest

from openapi_to_sdk.ir import UnsupportedSchemaError, build_api_ir


def test_nullable_openapi_30_uses_nullable_flag() -> None:
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "Nullable", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Legacy": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "integer", "nullable": True},
                    },
                }
            }
        },
    }

    ir = build_api_ir(doc)
    field = ir.schemas[0].fields[0]
    assert field.type_hint == "int | None"


def test_keyword_property_name_becomes_safe_python_name() -> None:
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Keyword", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Record": {
                    "type": "object",
                    "properties": {
                        "class": {"type": "string"},
                    },
                }
            }
        },
    }

    ir = build_api_ir(doc)
    field = ir.schemas[0].fields[0]
    assert field.python_name == "class_"


def test_unsupported_nested_union_in_allof_errors() -> None:
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Nested", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Bad": {
                    "allOf": [
                        {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "integer"},
                            ]
                        }
                    ]
                }
            }
        },
    }

    with pytest.raises(UnsupportedSchemaError, match="out of scope"):
        build_api_ir(doc)


def test_ambiguous_oneof_errors() -> None:
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Ambiguous", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Maybe": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "string"},
                    ]
                }
            }
        },
    }

    with pytest.raises(UnsupportedSchemaError, match="Ambiguous"):
        build_api_ir(doc)
