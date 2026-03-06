from __future__ import annotations

import json
from pathlib import Path

import pytest

from openapi_to_sdk.parser import OpenAPILoadError, load_openapi_document


def _write(path: Path, content: str) -> None:
    """Run write.

    Args:
        path: Argument value.
        content: Argument value.
    """
    path.write_text(content, encoding="utf-8")


def test_loads_json_openapi_document(tmp_path: Path) -> None:
    """Test loads json openapi document.

    Args:
        tmp_path: Argument value.
    """
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Demo", "version": "1.0.0"},
                "paths": {},
            }
        ),
        encoding="utf-8",
    )

    loaded = load_openapi_document(spec)

    assert loaded["openapi"] == "3.1.0"
    assert loaded["info"]["title"] == "Demo"


def test_loads_yaml_document_when_yaml_available(tmp_path: Path) -> None:
    """Test loads yaml document when yaml available.

    Args:
        tmp_path: Argument value.
    """
    spec = tmp_path / "spec.yaml"
    _write(
        spec,
        """
openapi: 3.0.3
info:
  title: YAML Demo
  version: 1.0.0
paths: {}
""".strip(),
    )

    try:
        loaded = load_openapi_document(spec)
    except OpenAPILoadError as exc:
        assert "PyYAML" in str(exc)
        return

    assert loaded["openapi"] == "3.0.3"
    assert loaded["info"]["title"] == "YAML Demo"


@pytest.mark.parametrize("version", ["3.0.3", "3.1.0"])
def test_supports_openapi_30_and_31(tmp_path: Path, version: str) -> None:
    """Test supports openapi 30 and 31.

    Args:
        tmp_path: Argument value.
        version: Argument value.
    """
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": version,
                "info": {"title": "Compat", "version": "1.0.0"},
                "paths": {},
            }
        ),
        encoding="utf-8",
    )

    loaded = load_openapi_document(spec)
    assert loaded["openapi"] == version


def test_resolves_relative_ref_file(tmp_path: Path) -> None:
    """Test resolves relative ref file.

    Args:
        tmp_path: Argument value.
    """
    schema_file = tmp_path / "schemas.json"
    schema_file.write_text(
        json.dumps(
            {
                "components": {
                    "schemas": {
                        "Pet": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Pets", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {"Pet": {"$ref": "schemas.json#/components/schemas/Pet"}}
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_openapi_document(spec_file)
    schema = loaded["components"]["schemas"]["Pet"]

    assert schema["type"] == "object"
    assert "name" in schema["properties"]


def test_detects_circular_ref(tmp_path: Path) -> None:
    """Test detects circular ref.

    Args:
        tmp_path: Argument value.
    """
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Cycle", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        "A": {"$ref": "#/components/schemas/B"},
                        "B": {"$ref": "#/components/schemas/A"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(OpenAPILoadError, match="Circular \\$ref"):
        load_openapi_document(spec)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"info": {"title": "x", "version": "1"}, "paths": {}}, "openapi"),
        ({"openapi": "2.0.0", "info": {"title": "x", "version": "1"}, "paths": {}}, "Unsupported OpenAPI"),
        ({"openapi": "3.1.0", "paths": {}}, "info"),
        ({"openapi": "3.1.0", "info": {"title": "x", "version": "1"}}, "paths"),
    ],
)
def test_invalid_top_level_errors(tmp_path: Path, payload: dict[str, object], error: str) -> None:
    """Test invalid top level errors.

    Args:
        tmp_path: Argument value.
        payload: Argument value.
        error: Argument value.
    """
    spec = tmp_path / "bad.json"
    spec.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(OpenAPILoadError, match=error):
        load_openapi_document(spec)
