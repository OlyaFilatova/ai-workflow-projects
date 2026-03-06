"""Typed domain models and serialization for audit reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    """Supported vulnerability severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(slots=True, frozen=True)
class PackageNode:
    """A resolved package node in the dependency graph."""

    name: str
    version: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the node for report output."""
        return {"name": self.name, "version": self.version}


@dataclass(slots=True, frozen=True)
class DependencyEdge:
    """A directed dependency relationship between two packages."""

    source: str
    target: str
    requirement: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Serialize the edge for report output."""
        return {
            "source": self.source,
            "target": self.target,
            "requirement": self.requirement,
        }


@dataclass(slots=True, frozen=True)
class VulnerabilityFinding:
    """A vulnerability detected for a resolved package."""

    package: str
    version: str
    vuln_id: str
    severity: Severity
    summary: str | None = None
    paths: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the vulnerability finding for report output."""
        return {
            "package": self.package,
            "version": self.version,
            "id": self.vuln_id,
            "severity": self.severity.value,
            "summary": self.summary,
            "paths": [list(path) for path in self.paths],
        }


@dataclass(slots=True, frozen=True)
class LicenseFinding:
    """A normalized license evaluation result for a package."""

    package: str
    version: str
    declared: str | None
    normalized_spdx: str | None
    policy_name: str
    policy_result: str
    paths: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the license finding for report output."""
        return {
            "package": self.package,
            "version": self.version,
            "declared": self.declared,
            "normalized_spdx": self.normalized_spdx,
            "policy": self.policy_name,
            "policy_result": self.policy_result,
            "paths": [list(path) for path in self.paths],
        }


@dataclass(slots=True)
class Report:
    """Top-level report model containing scan results and metadata."""

    python_version: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    nodes: list[PackageNode] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    vulnerabilities: list[VulnerabilityFinding] = field(default_factory=list)
    licenses: list[LicenseFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report with deterministic ordering."""
        ordered_nodes = sorted(self.nodes, key=lambda node: (node.name.lower(), node.version))
        ordered_edges = sorted(self.edges, key=lambda edge: (edge.source.lower(), edge.target.lower(), edge.requirement or ""))
        ordered_vulns = sorted(
            self.vulnerabilities,
            key=lambda vuln: (
                vuln.severity.value,
                vuln.package.lower(),
                vuln.version,
                vuln.vuln_id,
            ),
        )
        ordered_licenses = sorted(
            self.licenses,
            key=lambda finding: (finding.policy_result, finding.package.lower(), finding.version),
        )

        return {
            "metadata": {
                "timestamp": self.timestamp,
                "python_version": self.python_version,
            },
            "dependency_graph": {
                "nodes": [node.to_dict() for node in ordered_nodes],
                "edges": [edge.to_dict() for edge in ordered_edges],
            },
            "vulnerabilities": [vuln.to_dict() for vuln in ordered_vulns],
            "license_findings": [finding.to_dict() for finding in ordered_licenses],
        }
