"""CLI entrypoint for auditpy."""

from __future__ import annotations

import argparse

from auditpy.config import ScanConfig


def _parse_policy(value: str) -> str:
    if value != "no-gpl":
        raise argparse.ArgumentTypeError(
            f"Unsupported policy '{value}'. Only 'no-gpl' is currently supported."
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auditpy", description="Python dependency auditor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan dependencies from requirements")
    scan_parser.add_argument("-r", "--requirements", required=True, help="Path to requirements.txt")
    scan_parser.add_argument("--json", dest="json_path", help="Write JSON report to path")
    scan_parser.add_argument("--policy", type=_parse_policy, default="no-gpl", help="License policy name")
    scan_parser.add_argument(
        "--fail-on",
        choices=["high", "critical"],
        default="high",
        help="Fail threshold for vulnerability severities",
    )
    scan_parser.add_argument("--cache-ttl-hours", type=int, default=24, help="OSV cache TTL in hours")
    scan_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    scan_parser.set_defaults(func=_run_scan)

    return parser


def _run_scan(args: argparse.Namespace) -> int:
    # Configuration validation is centralized in ScanConfig.
    ScanConfig.create(
        policy=args.policy,
        fail_on=args.fail_on,
        cache_ttl_hours=args.cache_ttl_hours,
        verbose=args.verbose,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
