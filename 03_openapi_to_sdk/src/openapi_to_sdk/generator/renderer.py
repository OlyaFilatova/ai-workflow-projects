"""Template rendering orchestration."""

from pathlib import Path

from openapi_to_sdk.ir.models import ApiIR


def render_sdk(ir: ApiIR, output_dir: Path) -> None:
    """Render a generated SDK package from IR.

    This scaffold creates target directories. Later prompts expand full rendering.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    package_dir = output_dir / ir.title.lower().replace(" ", "_")
    package_dir.mkdir(parents=True, exist_ok=True)
    init_file = package_dir / "__init__.py"
    init_file.write_text(f"\"\"\"Generated SDK for {ir.title}.\"\"\"\n", encoding="utf-8")
