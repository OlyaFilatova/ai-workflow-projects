"""Vulnerability scanning functionality."""

from auditpy.models import VulnerabilityFinding


def scan_vulnerabilities() -> list[VulnerabilityFinding]:
    """Scan resolved packages for known vulnerabilities."""
    raise NotImplementedError("Implemented in later stage")
