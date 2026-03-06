"""Requirements parsing functionality."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from packaging.markers import default_environment
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name
except ModuleNotFoundError:
    from pip._vendor.packaging.markers import default_environment
    from pip._vendor.packaging.requirements import InvalidRequirement, Requirement
    from pip._vendor.packaging.utils import canonicalize_name


class RequirementsParseError(ValueError):
    """Raised when an unsupported or invalid requirements entry is encountered."""


@dataclass(slots=True, frozen=True)
class RootRequirement:
    name: str
    specifier: str
    extras: tuple[str, ...]
    marker: str | None
    source_file: str
    line_number: int
    raw: str

    @property
    def normalized_name(self) -> str:
        return canonicalize_name(self.name)


@dataclass(slots=True)
class ParseResult:
    requirements: list[RootRequirement]
    warnings: list[str]


def parse_requirements(requirements_file: str) -> ParseResult:
    """Parse requirements recursively with marker support and deterministic order."""
    root = Path(requirements_file)
    if not root.exists():
        raise RequirementsParseError(f"Requirements file not found: {requirements_file}")

    requirements: list[RootRequirement] = []
    warnings: list[str] = []
    _parse_file(root, requirements, warnings, visited=set(), stack=[])
    return ParseResult(requirements=requirements, warnings=warnings)


def _parse_file(
    file_path: Path,
    requirements: list[RootRequirement],
    warnings: list[str],
    *,
    visited: set[Path],
    stack: list[Path],
) -> None:
    resolved = file_path.resolve()
    if resolved in stack:
        chain = " -> ".join(str(path) for path in [*stack, resolved])
        raise RequirementsParseError(f"Recursive -r include detected: {chain}")
    if resolved in visited:
        return

    stack.append(resolved)
    lines = resolved.read_text(encoding="utf-8").splitlines()
    for index, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        include_path = _resolve_include_path(stripped, resolved, index)
        if include_path is not None:
            _parse_file(include_path, requirements, warnings, visited=visited, stack=stack)
            continue

        _raise_if_unsupported_entry(stripped, resolved, index)

        try:
            req = Requirement(stripped)
        except InvalidRequirement as exc:
            raise RequirementsParseError(f"{resolved}:{index} invalid requirement: {stripped}") from exc

        if req.marker is not None and not req.marker.evaluate(default_environment()):
            warnings.append(f"{resolved}:{index} skipped by environment marker: {stripped}")
            continue

        root_req = RootRequirement(
            name=req.name,
            specifier=str(req.specifier),
            extras=tuple(sorted(req.extras)),
            marker=str(req.marker) if req.marker else None,
            source_file=str(resolved),
            line_number=index,
            raw=stripped,
        )
        requirements.append(root_req)

    stack.pop()
    visited.add(resolved)


def _looks_like_direct_reference(line: str) -> bool:
    lowered = line.lower()
    if lowered.startswith(("git+", "hg+", "svn+", "bzr+", "http://", "https://")):
        return True
    if " @ " in line and ("http://" in lowered or "https://" in lowered or "git+" in lowered):
        return True
    return False


def _resolve_include_path(line: str, base_file: Path, line_number: int) -> Path | None:
    if not line.startswith(("-r ", "--requirement ")):
        return None

    include_target = line.split(maxsplit=1)[1].strip()
    include_path = (base_file.parent / include_target).resolve()
    if include_path.exists():
        return include_path

    raise RequirementsParseError(f"{base_file}:{line_number} included file not found: {include_target}")


def _raise_if_unsupported_entry(line: str, file_path: Path, line_number: int) -> None:
    if line.startswith(("-e ", "--editable ")):
        raise RequirementsParseError(
            f"{file_path}:{line_number} editable installs are unsupported: {line}"
        )
    if _looks_like_direct_reference(line):
        raise RequirementsParseError(
            f"{file_path}:{line_number} direct URL/VCS dependencies are unsupported: {line}"
        )
