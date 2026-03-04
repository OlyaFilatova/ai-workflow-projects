from __future__ import annotations

import json
from pathlib import Path

import pytest

from openapi_to_sdk.parser import OpenAPILoadError, load_openapi_document


def test_loader_rejects_remote_ref(tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Remote", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        "User": {"$ref": "https://example.com/schemas.json#/User"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(OpenAPILoadError, match="Remote refs"):
        load_openapi_document(spec)


def test_loader_errors_on_missing_ref_target_file(tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Missing", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        "User": {"$ref": "missing.json#/components/schemas/User"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(OpenAPILoadError, match="target file not found"):
        load_openapi_document(spec)


def test_loader_errors_on_invalid_pointer(tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Pointer", "version": "1.0.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        "User": {"$ref": "#/components/schemas/DoesNotExist"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(OpenAPILoadError, match="Unable to resolve JSON pointer"):
        load_openapi_document(spec)
