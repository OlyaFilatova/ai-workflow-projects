"""CLI entrypoint for openapi-to-sdk."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openapi_to_sdk.generator import GenerationPipelineError, generate_sdk_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openapi-to-sdk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate SDK package from OpenAPI spec")
    generate.add_argument("--spec", type=Path, required=True, help="Path to OpenAPI file")
    generate.add_argument("--output", type=Path, required=True, help="Output directory")
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
        generated_dir = generate_sdk_package(
            spec_path=args.spec,
            output_dir=args.output,
            overwrite=args.overwrite,
        )
    except GenerationPipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated SDK into: {generated_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
