"""CLI entrypoint for auditpy."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import cast

from auditpy.config import ScanConfig
from auditpy.licenses import evaluate_licenses
from auditpy.models import Report
from auditpy.policy import threshold_violated
from auditpy.reporting import render_cli_summary, write_json_report
from auditpy.resolution import resolve_dependencies
from auditpy.vulnerabilities import scan_vulnerabilities


def _parse_policy(value: str) -> str:
    """Validate and normalize the supported policy CLI option.

    Args:
        value: Raw policy value supplied via CLI arguments.
    """
    if value != "no-gpl":
        raise argparse.ArgumentTypeError(
            f"Unsupported policy '{value}'. Only 'no-gpl' is currently supported."
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level CLI argument parser."""
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
    scan_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    scan_parser.set_defaults(func=_run_scan)

    return parser


def _run_scan(args: argparse.Namespace) -> int:
    """Execute the scan command and return the process exit code.

    Args:
        args: Parsed CLI namespace for the `scan` subcommand.
    """
    cfg = ScanConfig.create(
        policy=args.policy,
        fail_on=args.fail_on,
        cache_ttl_hours=24,
        verbose=args.verbose,
    )

    resolution = resolve_dependencies(args.requirements)
    if not resolution.ok:
        assert resolution.error is not None
        print(f"Runtime error: {resolution.error.message}", file=sys.stderr)
        return resolution.error.exit_code

    vuln_result = scan_vulnerabilities(
        resolution.nodes,
        resolution.dependency_paths,
        cache_ttl_hours=cfg.cache_ttl_hours,
    )
    license_result = evaluate_licenses(
        resolution.distributions,
        resolution.dependency_paths,
        policy=cfg.policy,
    )

    report = Report(
        python_version=sys.version.split()[0],
        nodes=resolution.nodes,
        edges=resolution.edges,
        vulnerabilities=vuln_result.findings,
        licenses=license_result.findings,
    )

    if args.json_path:
        write_json_report(report, args.json_path)

    print(render_cli_summary(report))

    for warning in [*resolution.warnings, *vuln_result.warnings, *license_result.warnings]:
        print(f"warning: {warning}", file=sys.stderr)

    if threshold_violated(report, fail_on=cfg.fail_on):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by both module and console script execution.

    Args:
        argv: Optional argument list. When None, arguments are read from `sys.argv`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    command = cast(Callable[[argparse.Namespace], int], args.func)
    return command(args)
