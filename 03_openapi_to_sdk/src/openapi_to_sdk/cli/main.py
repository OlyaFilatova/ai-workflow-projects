"""CLI entrypoint for openapi-to-sdk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from openapi_to_sdk.generator import GenerationPipelineError, generate_sdk_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openapi-to-sdk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate SDK package from OpenAPI spec")
    generate.add_argument("--config", type=Path, help="Optional JSON config file")
    generate.add_argument("--spec", type=Path, help="Path to OpenAPI file")
    generate.add_argument("--output", type=Path, help="Output directory")
    generate.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output directory when it already exists",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "generate":
        parser.error("Unsupported command")
        return 2

    try:
        spec_path, output_dir, overwrite = _resolve_generate_args(args)
        generated_dir = generate_sdk_package(
            spec_path=spec_path,
            output_dir=output_dir,
            overwrite=overwrite,
        )
    except GenerationPipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated SDK into: {generated_dir}")
    return 0


def _resolve_generate_args(args: argparse.Namespace) -> tuple[Path, Path, bool]:
    config: dict[str, Any] = {}
    if args.config is not None:
        config = _load_json_config(args.config)

    spec = args.spec if args.spec is not None else _as_path(config.get("spec"))
    output = args.output if args.output is not None else _as_path(config.get("output"))
    overwrite = bool(args.overwrite or config.get("overwrite", False))

    if spec is None:
        raise GenerationPipelineError("Missing required '--spec' (or 'spec' in config)")
    if output is None:
        raise GenerationPipelineError("Missing required '--output' (or 'output' in config)")

    return spec, output, overwrite


def _load_json_config(path: Path) -> dict[str, Any]:
    config_path = path.expanduser().resolve()
    if not config_path.exists():
        raise GenerationPipelineError(f"Config file does not exist: {config_path}")

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GenerationPipelineError(f"Invalid JSON config file '{config_path}': {exc}") from exc

    if not isinstance(payload, dict):
        raise GenerationPipelineError(f"Config file must contain a JSON object: {config_path}")
    return payload


def _as_path(value: Any) -> Path | None:
    if isinstance(value, str) and value.strip():
        return Path(value)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
