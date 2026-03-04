"""OpenAPI loading interfaces used by the generation pipeline."""

from pathlib import Path
from typing import Any


def load_openapi_document(spec_path: Path) -> dict[str, Any]:
    """Load an OpenAPI document from disk.

    This scaffold implementation returns a minimal structure and will be expanded
    by later prompts.
    """
    return {
        "openapi": "3.1.0",
        "info": {"title": spec_path.stem, "version": "0.0.0"},
        "paths": {},
    }
