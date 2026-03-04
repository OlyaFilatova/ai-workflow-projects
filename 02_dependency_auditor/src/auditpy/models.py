"""Core model stubs for the dependency auditor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PackageNode:
    name: str
    version: str


@dataclass(slots=True)
class DependencyEdge:
    source: str
    target: str
    requirement: str | None = None


@dataclass(slots=True)
class VulnerabilityFinding:
    package: str
    version: str
    vuln_id: str
    severity: str
    summary: str | None = None
    paths: list[list[str]] = field(default_factory=list)


@dataclass(slots=True)
class LicenseFinding:
    package: str
    version: str
    declared: str | None
    normalized_spdx: str | None
    policy_violation: bool
    paths: list[list[str]] = field(default_factory=list)


@dataclass(slots=True)
class Report:
    metadata: dict[str, Any]
    nodes: list[PackageNode] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    vulnerabilities: list[VulnerabilityFinding] = field(default_factory=list)
    licenses: list[LicenseFinding] = field(default_factory=list)
