"""Reporting helpers for CLI and JSON outputs."""

from auditpy.models import Report


def render_cli_summary(report: Report) -> str:
    """Render a short CLI summary from report data."""
    lines = [
        f"Total packages: {len(report.nodes)}",
        f"Vulnerabilities: {len(report.vulnerabilities)}",
        f"License findings: {len(report.licenses)}",
    ]
    return "\n".join(lines)
