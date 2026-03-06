"""OpenAPI loading and local $ref resolution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openapi_to_sdk.parser.errors import OpenAPILoadError


def load_openapi_document(spec_path: Path) -> dict[str, Any]:
    """Load, validate, and resolve local references in an OpenAPI document."""
    path = spec_path.expanduser().resolve()
    if not path.exists():
        raise OpenAPILoadError(f"Spec file does not exist: {path}")

    cache: dict[Path, dict[str, Any]] = {}
    document = _load_file(path, cache)
    _validate_openapi_top_level(document, path)
    resolved = _resolve_node(document, current_file=path, cache=cache, stack=set())
    return _sorted_dicts(resolved)


def _load_file(path: Path, cache: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    if path in cache:
        return cache[path]

    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    try:
        if suffix == ".json":
            parsed = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            parsed = _load_yaml(text)
        else:
            raise OpenAPILoadError(
                f"Unsupported spec extension '{path.suffix}'. Use .json, .yaml, or .yml"
            )
    except json.JSONDecodeError as exc:
        raise OpenAPILoadError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(parsed, dict):
        raise OpenAPILoadError(f"OpenAPI root must be an object in file: {path}")

    cache[path] = parsed
    return parsed


def _load_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise OpenAPILoadError(
            "YAML parsing requires PyYAML. Install with 'pip install pyyaml'."
        ) from exc

    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise OpenAPILoadError(f"Invalid YAML OpenAPI document: {exc}") from exc
    if not isinstance(parsed, dict):
        raise OpenAPILoadError("YAML OpenAPI root must be an object")
    return parsed


def _validate_openapi_top_level(document: dict[str, Any], path: Path) -> None:
    version = document.get("openapi")
    if not isinstance(version, str):
        raise OpenAPILoadError(f"Missing or invalid 'openapi' field in {path}")
    if not (version.startswith("3.0") or version.startswith("3.1")):
        raise OpenAPILoadError(
            f"Unsupported OpenAPI version '{version}' in {path}; only 3.0/3.1 are supported"
        )

    info = document.get("info")
    if not isinstance(info, dict):
        raise OpenAPILoadError(f"Missing or invalid 'info' object in {path}")
    if not isinstance(info.get("title"), str) or not info["title"].strip():
        raise OpenAPILoadError(f"'info.title' must be a non-empty string in {path}")
    if not isinstance(info.get("version"), str) or not info["version"].strip():
        raise OpenAPILoadError(f"'info.version' must be a non-empty string in {path}")

    paths_obj = document.get("paths")
    if not isinstance(paths_obj, dict):
        raise OpenAPILoadError(f"Missing or invalid 'paths' object in {path}")


def _resolve_node(
    node: Any,
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> Any:
    if isinstance(node, dict):
        return _resolve_mapping_node(node, current_file=current_file, cache=cache, stack=stack)
    if isinstance(node, list):
        return _resolve_sequence_node(node, current_file=current_file, cache=cache, stack=stack)
    return node


def _resolve_mapping_node(
    node: dict[str, Any],
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> Any:
    if "$ref" in node:
        return _resolve_ref_mapping(node, current_file=current_file, cache=cache, stack=stack)
    return {
        key: _resolve_node(value, current_file=current_file, cache=cache, stack=stack)
        for key, value in node.items()
    }


def _resolve_ref_mapping(
    node: dict[str, Any],
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> Any:
    ref_value = node["$ref"]
    if not isinstance(ref_value, str):
        raise OpenAPILoadError(f"$ref must be a string in {current_file}")

    resolved_ref = _resolve_ref(
        ref_value,
        current_file=current_file,
        cache=cache,
        stack=stack,
    )
    if len(node) == 1:
        return resolved_ref
    return _merge_ref_overrides(
        resolved_ref,
        node,
        current_file=current_file,
        cache=cache,
        stack=stack,
    )


def _merge_ref_overrides(
    resolved_ref: Any,
    node: dict[str, Any],
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> dict[str, Any]:
    merged = dict(resolved_ref) if isinstance(resolved_ref, dict) else {"value": resolved_ref}
    for key, value in node.items():
        if key != "$ref":
            merged[key] = _resolve_node(
                value,
                current_file=current_file,
                cache=cache,
                stack=stack,
            )
    return merged


def _resolve_sequence_node(
    node: list[Any],
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> list[Any]:
    return [
        _resolve_node(item, current_file=current_file, cache=cache, stack=stack)
        for item in node
    ]


def _resolve_ref(
    ref: str,
    *,
    current_file: Path,
    cache: dict[Path, dict[str, Any]],
    stack: set[tuple[Path, str]],
) -> Any:
    if ref.startswith("http://") or ref.startswith("https://"):
        raise OpenAPILoadError(f"Remote refs are not supported in MVP: {ref}")

    file_part, fragment = _split_ref(ref)
    target_file = (current_file.parent / file_part).resolve() if file_part else current_file
    if not target_file.exists():
        raise OpenAPILoadError(f"$ref target file not found: {target_file} (from {current_file})")

    target_document = _load_file(target_file, cache)
    pointer = fragment or ""
    marker = (target_file, pointer)

    if marker in stack:
        raise OpenAPILoadError(
            f"Circular $ref detected at {target_file}#{pointer or '/'} from {current_file}"
        )

    stack.add(marker)
    try:
        target_value = _resolve_json_pointer(target_document, pointer)
        return _resolve_node(
            target_value,
            current_file=target_file,
            cache=cache,
            stack=stack,
        )
    finally:
        stack.remove(marker)


def _split_ref(ref: str) -> tuple[str, str]:
    if "#" in ref:
        file_part, fragment = ref.split("#", 1)
        return file_part, fragment
    return ref, ""


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return document
    if not pointer.startswith("/"):
        raise OpenAPILoadError(f"JSON pointer must start with '/': {pointer}")

    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        current = _resolve_pointer_segment(current, part, pointer)
    return current


def _resolve_pointer_segment(current: Any, part: str, pointer: str) -> Any:
    if isinstance(current, dict):
        if part not in current:
            raise OpenAPILoadError(f"Unable to resolve JSON pointer segment '{part}' in '{pointer}'")
        return current[part]

    if not isinstance(current, list):
        raise OpenAPILoadError(f"Unable to resolve JSON pointer segment '{part}' in '{pointer}'")

    try:
        index = int(part)
    except ValueError as exc:
        raise OpenAPILoadError(f"Invalid list index in JSON pointer: {part}") from exc
    if not (0 <= index < len(current)):
        raise OpenAPILoadError(f"List index out of range in JSON pointer: {part}")
    return current[index]


def _sorted_dicts(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sorted_dicts(v) for k, v in sorted(value.items(), key=lambda item: item[0])}
    if isinstance(value, list):
        return [_sorted_dicts(v) for v in value]
    return value
