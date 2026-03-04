"""CLI entrypoint for auditpy."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auditpy", description="Python dependency auditor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan dependencies from requirements")
    scan_parser.add_argument("-r", "--requirements", required=True, help="Path to requirements.txt")
    scan_parser.add_argument("--json", dest="json_path", help="Write JSON report to path")
    scan_parser.add_argument("--policy", default="no-gpl", help="License policy name")
    scan_parser.add_argument(
        "--fail-on",
        choices=["high", "critical"],
        default="high",
        help="Fail threshold for vulnerability severities",
    )
    scan_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    scan_parser.set_defaults(func=_run_scan)

    return parser


def _run_scan(args: argparse.Namespace) -> int:
    _ = args
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
