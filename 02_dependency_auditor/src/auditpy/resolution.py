"""Dependency resolution functionality."""

from auditpy.models import DependencyEdge, PackageNode


def resolve_dependencies(requirements_file: str) -> tuple[list[PackageNode], list[DependencyEdge]]:
    """Resolve dependency graph from requirements file."""
    raise NotImplementedError("Implemented in later stage")
