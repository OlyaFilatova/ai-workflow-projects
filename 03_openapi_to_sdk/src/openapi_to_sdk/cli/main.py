"""CLI entrypoint for openapi-to-sdk."""

from __future__ import annotations

import argparse
from pathlib import Path

from openapi_to_sdk.generator.renderer import render_sdk
from openapi_to_sdk.ir import build_api_ir
from openapi_to_sdk.parser.loader import load_openapi_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openapi-to-sdk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate SDK package from OpenAPI spec")
    generate.add_argument("--spec", type=Path, required=True, help="Path to OpenAPI file")
    generate.add_argument("--output", type=Path, required=True, help="Output directory")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        spec = load_openapi_document(args.spec)
        ir = build_api_ir(spec)
        render_sdk(ir=ir, output_dir=args.output)
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
