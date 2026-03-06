"""Dependency resolution functionality."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass, field
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from auditpy.models import DependencyEdge, PackageNode
from auditpy.parsing import parse_requirements


@dataclass(slots=True, frozen=True)
class ResolutionFailure:
    category: str
    message: str
    exit_code: int = 2


@dataclass(slots=True)
class ResolutionOutcome:
    nodes: list[PackageNode] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    dependency_paths: dict[str, list[list[str]]] = field(default_factory=dict)
    distributions: list[dict[str, object]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: ResolutionFailure | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def resolve_dependencies(requirements_file: str) -> ResolutionOutcome:
    """Resolve dependency graph from requirements file using a temporary virtual environment."""
    req_path = Path(requirements_file)
    if not req_path.exists():
        return _runtime_error_outcome(
            f"Requirements file not found: {requirements_file}",
        )

    try:
        parsed_requirements = parse_requirements(str(req_path))
    except Exception as exc:
        return _runtime_error_outcome(f"Requirements parsing failed: {exc}")

    root_package_names = [requirement.normalized_name for requirement in parsed_requirements.requirements]

    try:
        with tempfile.TemporaryDirectory(prefix="auditpy-resolve-") as tmp_dir:
            venv_dir = Path(tmp_dir) / "venv"
            _create_venv(venv_dir)
            python_bin = _venv_python(venv_dir)

            _pip_install_requirements(python_bin, req_path)
            installed_distributions = _collect_installed_distributions(python_bin)
    except Exception as exc:
        return _runtime_error_outcome(
            f"Dependency resolution failed: {exc}",
            warnings=parsed_requirements.warnings,
        )

    edges, adjacency = _build_edges(installed_distributions)
    nodes = sorted(
        (
            PackageNode(name=str(distribution["name"]), version=str(distribution["version"]))
            for distribution in installed_distributions
        ),
        key=lambda node: (node.name.lower(), node.version),
    )
    dependency_paths = _build_paths(root_package_names, adjacency)

    return ResolutionOutcome(
        nodes=nodes,
        edges=edges,
        dependency_paths=dependency_paths,
        distributions=installed_distributions,
        warnings=parsed_requirements.warnings,
    )


def _runtime_error_outcome(message: str, *, warnings: list[str] | None = None) -> ResolutionOutcome:
    return ResolutionOutcome(
        warnings=list(warnings or []),
        error=ResolutionFailure(category="runtime", message=message),
    )


def _create_venv(venv_dir: Path) -> None:
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(venv_dir)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _pip_install_requirements(python_bin: Path, requirements_file: Path) -> None:
    cmd = [
        str(python_bin),
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_file),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "Unknown pip install error"
        raise RuntimeError(f"Dependency resolution failed: {stderr}")


def _collect_installed_distributions(python_bin: Path) -> list[dict[str, object]]:
    script = (
        "import json\n"
        "from importlib import metadata\n"
        "items=[]\n"
        "for dist in metadata.distributions():\n"
        "    name = dist.metadata.get('Name')\n"
        "    if not name:\n"
        "        continue\n"
        "    classifiers = dist.metadata.get_all('Classifier') or []\n"
        "    items.append({\n"
        "      'name': name,\n"
        "      'version': dist.version,\n"
        "      'requires': list(dist.requires or []),\n"
        "      'license': dist.metadata.get('License'),\n"
        "      'classifiers': classifiers,\n"
        "    })\n"
        "print(json.dumps(items))\n"
    )
    result = subprocess.run([str(python_bin), "-c", script], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unable to inspect installed distributions"
        raise RuntimeError(f"Metadata inspection failed: {stderr}")

    distribution_metadata = json.loads(result.stdout)
    distribution_metadata.sort(
        key=lambda distribution: (str(distribution["name"]).lower(), str(distribution["version"]))
    )
    return distribution_metadata


def _build_edges(
    installed: list[dict[str, object]],
) -> tuple[list[DependencyEdge], dict[str, set[str]]]:
    package_names_by_normalized = {
        canonicalize_name(str(distribution["name"])): str(distribution["name"])
        for distribution in installed
    }
    adjacency: dict[str, set[str]] = {name: set() for name in package_names_by_normalized.keys()}
    edges: list[DependencyEdge] = []

    for distribution in installed:
        source_name = str(distribution["name"])
        source_norm = canonicalize_name(source_name)
        requirements = distribution.get("requires") or []

        for raw_req in requirements:
            raw_req_str = str(raw_req)
            try:
                req = Requirement(raw_req_str)
            except InvalidRequirement:
                continue

            target_norm = canonicalize_name(req.name)
            target_name = package_names_by_normalized.get(target_norm)
            if not target_name:
                continue

            adjacency[source_norm].add(target_norm)
            edges.append(
                DependencyEdge(
                    source=source_name,
                    target=target_name,
                    requirement=raw_req_str,
                )
            )

    edges.sort(key=lambda edge: (edge.source.lower(), edge.target.lower(), edge.requirement or ""))
    return edges, adjacency


def _build_paths(
    root_names: list[str],
    adjacency: dict[str, set[str]],
) -> dict[str, list[list[str]]]:
    paths_by_target: dict[str, list[list[str]]] = {}

    for root in root_names:
        if root not in adjacency:
            continue
        stack: list[tuple[str, list[str]]] = [(root, [root])]
        visited_edges: set[tuple[str, str]] = set()

        while stack:
            current, path = stack.pop()
            paths_by_target.setdefault(current, []).append(list(path))

            for neighbor in sorted(adjacency.get(current, set())):
                edge = (current, neighbor)
                if edge in visited_edges:
                    continue
                visited_edges.add(edge)
                if neighbor in path:
                    continue
                stack.append((neighbor, [*path, neighbor]))

    for target, paths in paths_by_target.items():
        unique = {tuple(path) for path in paths}
        paths_by_target[target] = [list(path) for path in sorted(unique)]

    return paths_by_target
