"""Dependency resolution functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

try:
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name
except ModuleNotFoundError:
    from pip._vendor.packaging.requirements import InvalidRequirement, Requirement
    from pip._vendor.packaging.utils import canonicalize_name

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
        return ResolutionOutcome(
            error=ResolutionFailure(
                category="runtime",
                message=f"Requirements file not found: {requirements_file}",
            )
        )

    parsed = parse_requirements(str(req_path))
    root_names = [req.normalized_name for req in parsed.requirements]

    try:
        with tempfile.TemporaryDirectory(prefix="auditpy-resolve-") as tmp_dir:
            venv_dir = Path(tmp_dir) / "venv"
            _create_venv(venv_dir)
            python_bin = _venv_python(venv_dir)

            _pip_install_requirements(python_bin, req_path)
            installed = _collect_installed_distributions(python_bin)
    except Exception as exc:
        return ResolutionOutcome(
            warnings=parsed.warnings,
            error=ResolutionFailure(category="runtime", message=str(exc)),
        )

    edges, adjacency = _build_edges(installed)
    nodes = sorted(
        (PackageNode(name=str(item["name"]), version=str(item["version"])) for item in installed),
        key=lambda node: (node.name.lower(), node.version),
    )
    dependency_paths = _build_paths(root_names, adjacency)

    return ResolutionOutcome(
        nodes=nodes,
        edges=edges,
        dependency_paths=dependency_paths,
        distributions=installed,
        warnings=parsed.warnings,
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

    parsed = json.loads(result.stdout)
    parsed.sort(key=lambda item: (str(item["name"]).lower(), str(item["version"])))
    return parsed


def _build_edges(
    installed: list[dict[str, object]],
) -> tuple[list[DependencyEdge], dict[str, set[str]]]:
    known = {canonicalize_name(str(item["name"])): str(item["name"]) for item in installed}
    adjacency: dict[str, set[str]] = {name: set() for name in known.keys()}
    edges: list[DependencyEdge] = []

    for item in installed:
        source_name = str(item["name"])
        source_norm = canonicalize_name(source_name)
        requirements = item.get("requires") or []

        for raw_req in requirements:
            raw_req_str = str(raw_req)
            try:
                req = Requirement(raw_req_str)
            except InvalidRequirement:
                continue

            target_norm = canonicalize_name(req.name)
            target_name = known.get(target_norm)
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
