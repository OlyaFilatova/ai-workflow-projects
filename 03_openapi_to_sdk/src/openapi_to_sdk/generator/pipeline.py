"""End-to-end generation pipeline orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir import UnsupportedSchemaError, build_api_ir
from openapi_to_sdk.parser import OpenAPILoadError, load_openapi_document


class GenerationPipelineError(RuntimeError):
    """Raised when generation cannot be completed."""


def generate_sdk_package(
    *,
    spec_path: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> Path:
    """Generate an SDK package from an OpenAPI spec path.

    Args:
        spec_path: Path to the input OpenAPI document.
        output_dir: Directory where generated package files are written.
        overwrite: Whether to replace an existing non-empty output directory.
    """
    spec = spec_path.expanduser().resolve()
    out = output_dir.expanduser().resolve()

    if out.exists() and any(out.iterdir()) and not overwrite:
        raise GenerationPipelineError(
            f"Output directory already exists and is not empty: {out}. "
            "Use --overwrite to replace it."
        )

    if out.exists() and overwrite:
        shutil.rmtree(out)

    out.mkdir(parents=True, exist_ok=True)

    try:
        document = load_openapi_document(spec)
        ir = build_api_ir(document)
    except (OpenAPILoadError, UnsupportedSchemaError) as exc:
        raise GenerationPipelineError(str(exc)) from exc

    render_sdk(ir, out)
    return out
